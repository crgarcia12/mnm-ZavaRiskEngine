using System;
using System.Collections.Generic;
using System.Data;
using System.Data.SqlClient;
using System.Globalization;
using System.ServiceModel;

namespace ZavaRiskEngine
{
    public class ZavaRiskEngineService : IRiskEngineService
    {
        public RiskScoreResponse ScoreLoanApplication(int applicationId)
        {
            if (applicationId <= 0)
            {
                throw new FaultException("applicationId must be greater than 0.");
            }

            using (var connection = new SqlConnection(DbConfig.GetConnectionString()))
            {
                connection.Open();
                EnsureRiskModelTableExists(connection);

                int customerId;
                decimal requestedAmount;
                int termMonths;
                decimal accountBalance;
                int creditScore;

                using (var command = new SqlCommand(@"
SELECT TOP 1
    la.CustomerID,
    la.RequestedAmount,
    la.TermMonths,
    ISNULL(a.Balance, 0) AS Balance,
    ISNULL((
        SELECT TOP 1 cs.Score
        FROM CreditScores cs
        WHERE cs.CustomerID = la.CustomerID
        ORDER BY cs.ReportDate DESC
    ), 650) AS CreditScore
FROM LoanApplications la
LEFT JOIN Accounts a ON a.AccountID = la.LoanAccountID
WHERE la.ApplicationID = @ApplicationID;", connection))
                {
                    command.Parameters.AddWithValue("@ApplicationID", applicationId);
                    using (var reader = command.ExecuteReader())
                    {
                        if (!reader.Read())
                        {
                            throw new FaultException("Loan application was not found.");
                        }

                        customerId = reader.GetInt32(0);
                        requestedAmount = reader.GetDecimal(1);
                        termMonths = reader.GetInt32(2);
                        accountBalance = reader.GetDecimal(3);
                        creditScore = reader.GetInt32(4);
                    }
                }

                var model = LoadModelParameters(connection);
                var weightedScore =
                    NormalizeCreditScore(creditScore) * GetModelValue(model, "CreditScoreWeight", 0.45m) +
                    NormalizeBalance(accountBalance, requestedAmount) * GetModelValue(model, "BalanceWeight", 0.20m) +
                    NormalizeTerm(termMonths) * GetModelValue(model, "TermWeight", 0.10m) +
                    NormalizeLoanAmount(requestedAmount) * GetModelValue(model, "RequestedAmountWeight", 0.25m);

                var baseScore = GetModelValue(model, "BaseScore", 5m);
                var finalScore = decimal.Round(baseScore + weightedScore * 100m, 2, MidpointRounding.AwayFromZero);
                var rating = GetRating(finalScore);
                var maxApprovedAmount = decimal.Round(requestedAmount * GetApprovalMultiplier(rating), 2, MidpointRounding.AwayFromZero);

                using (var saveAssessment = new SqlCommand(@"
INSERT INTO RiskAssessments (ApplicationID, CustomerID, OverallRiskScore, RiskLevel, Recommendation, FactorBreakdown)
VALUES (@ApplicationID, @CustomerID, @OverallRiskScore, @RiskLevel, @Recommendation, @FactorBreakdown);", connection))
                {
                    saveAssessment.Parameters.AddWithValue("@ApplicationID", applicationId);
                    saveAssessment.Parameters.AddWithValue("@CustomerID", customerId);
                    saveAssessment.Parameters.AddWithValue("@OverallRiskScore", finalScore);
                    saveAssessment.Parameters.AddWithValue("@RiskLevel", rating);
                    saveAssessment.Parameters.AddWithValue("@Recommendation", rating == "F" ? "Deny" : "Review");
                    saveAssessment.Parameters.AddWithValue("@FactorBreakdown", string.Format(CultureInfo.InvariantCulture,
                        "CreditScore={0};RequestedAmount={1};TermMonths={2};Balance={3}", creditScore, requestedAmount, termMonths, accountBalance));
                    saveAssessment.ExecuteNonQuery();
                }

                return new RiskScoreResponse
                {
                    ApplicationId = applicationId,
                    CustomerId = customerId,
                    RequestedAmount = requestedAmount,
                    MaxApprovedAmount = maxApprovedAmount,
                    CalculatedScore = finalScore,
                    RiskRating = rating,
                    EvaluatedAtUtc = DateTime.UtcNow
                };
            }
        }

        public RiskFactorsResponse GetRiskFactors(int customerId)
        {
            if (customerId <= 0)
            {
                throw new FaultException("customerId must be greater than 0.");
            }

            using (var connection = new SqlConnection(DbConfig.GetConnectionString()))
            {
                connection.Open();

                int creditScore;
                decimal openLoanExposure;
                decimal avgBalance;
                int activeAccountCount;

                using (var command = new SqlCommand(@"
SELECT
    ISNULL((SELECT TOP 1 Score FROM CreditScores WHERE CustomerID = @CustomerID ORDER BY ReportDate DESC), 650) AS CreditScore,
    ISNULL((SELECT SUM(RequestedAmount) FROM LoanApplications WHERE CustomerID = @CustomerID AND Status IN ('Submitted','UnderReview','Approved')), 0) AS OpenLoanExposure,
    ISNULL((SELECT AVG(Balance) FROM Accounts WHERE CustomerID = @CustomerID), 0) AS AverageBalance,
    ISNULL((SELECT COUNT(*) FROM Accounts WHERE CustomerID = @CustomerID AND Status = 'Active'), 0) AS ActiveAccountCount;", connection))
                {
                    command.Parameters.AddWithValue("@CustomerID", customerId);
                    using (var reader = command.ExecuteReader())
                    {
                        if (!reader.Read())
                        {
                            throw new FaultException("Customer risk profile was not found.");
                        }

                        creditScore = Convert.ToInt32(reader[0], CultureInfo.InvariantCulture);
                        openLoanExposure = Convert.ToDecimal(reader[1], CultureInfo.InvariantCulture);
                        avgBalance = Convert.ToDecimal(reader[2], CultureInfo.InvariantCulture);
                        activeAccountCount = Convert.ToInt32(reader[3], CultureInfo.InvariantCulture);
                    }
                }

                var factorMetadata = LoadFactorMetadata(connection);
                var factors = new List<RiskFactorItem>
                {
                    BuildFactor(factorMetadata, "CREDIT_SCORE", NormalizeCreditScore(creditScore)),
                    BuildFactor(factorMetadata, "EXIST_DEBT", decimal.Round(100m - Clamp(openLoanExposure / 5000m, 0m, 100m), 2, MidpointRounding.AwayFromZero)),
                    BuildFactor(factorMetadata, "ASSET_RES", Clamp(avgBalance / 200m, 0m, 100m)),
                    BuildFactor(factorMetadata, "ACCT_AGE", Clamp(activeAccountCount * 12m, 0m, 100m))
                };

                decimal weightedTotal = 0m;
                decimal weightSum = 0m;
                foreach (var factor in factors)
                {
                    weightedTotal += factor.ImpactScore;
                    weightSum += factor.Weight <= 0m ? 1m : factor.Weight;
                }

                var overall = weightSum == 0m ? 0m : decimal.Round(weightedTotal / weightSum, 2, MidpointRounding.AwayFromZero);

                return new RiskFactorsResponse
                {
                    CustomerId = customerId,
                    OverallScore = overall,
                    Factors = factors
                };
            }
        }

        public RiskModelUpdateResponse UpdateRiskModel(RiskModelUpdateRequest modelParams)
        {
            if (modelParams == null || modelParams.Parameters == null || modelParams.Parameters.Count == 0)
            {
                throw new FaultException("modelParams with at least one parameter is required.");
            }

            using (var connection = new SqlConnection(DbConfig.GetConnectionString()))
            {
                connection.Open();
                EnsureRiskModelTableExists(connection);

                int updatedCount = 0;
                using (var transaction = connection.BeginTransaction())
                {
                    foreach (var parameter in modelParams.Parameters)
                    {
                        if (parameter == null || string.IsNullOrWhiteSpace(parameter.Name))
                        {
                            continue;
                        }

                        using (var command = new SqlCommand(@"
IF EXISTS (SELECT 1 FROM RiskModelParameters WHERE ParameterName = @ParameterName)
BEGIN
    UPDATE RiskModelParameters
    SET ParameterValue = @ParameterValue,
        ModifiedDate = GETDATE(),
        ModifiedBy = @ModifiedBy
    WHERE ParameterName = @ParameterName;
END
ELSE
BEGIN
    INSERT INTO RiskModelParameters (ParameterName, ParameterValue, ModifiedBy)
    VALUES (@ParameterName, @ParameterValue, @ModifiedBy);
END", connection, transaction))
                        {
                            command.Parameters.AddWithValue("@ParameterName", parameter.Name.Trim());
                            command.Parameters.AddWithValue("@ParameterValue", parameter.Value);
                            command.Parameters.AddWithValue("@ModifiedBy", string.IsNullOrWhiteSpace(modelParams.UpdatedBy) ? "SYSTEM" : modelParams.UpdatedBy.Trim());
                            updatedCount += command.ExecuteNonQuery() > 0 ? 1 : 0;
                        }
                    }

                    transaction.Commit();
                }

                return new RiskModelUpdateResponse
                {
                    Success = true,
                    UpdatedCount = updatedCount,
                    Message = "Risk model parameters updated.",
                    UpdatedAtUtc = DateTime.UtcNow
                };
            }
        }

        private static void EnsureRiskModelTableExists(SqlConnection connection)
        {
            using (var command = new SqlCommand(@"
IF OBJECT_ID('dbo.RiskModelParameters', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.RiskModelParameters
    (
        ParameterName NVARCHAR(100) NOT NULL PRIMARY KEY,
        ParameterValue DECIMAL(18,6) NOT NULL,
        ModifiedDate DATETIME NOT NULL DEFAULT GETDATE(),
        ModifiedBy NVARCHAR(100) NULL
    );
END", connection))
            {
                command.ExecuteNonQuery();
            }
        }

        private static Dictionary<string, decimal> LoadModelParameters(SqlConnection connection)
        {
            var parameters = new Dictionary<string, decimal>(StringComparer.OrdinalIgnoreCase);

            using (var command = new SqlCommand("SELECT ParameterName, ParameterValue FROM RiskModelParameters;", connection))
            using (var reader = command.ExecuteReader())
            {
                while (reader.Read())
                {
                    parameters[reader.GetString(0)] = reader.GetDecimal(1);
                }
            }

            return parameters;
        }

        private static Dictionary<string, RiskFactorItem> LoadFactorMetadata(SqlConnection connection)
        {
            var metadata = new Dictionary<string, RiskFactorItem>(StringComparer.OrdinalIgnoreCase);

            using (var command = new SqlCommand(@"
SELECT FactorCode, FactorName, Weight
FROM RiskFactors
WHERE IsActive = 1;", connection))
            using (var reader = command.ExecuteReader())
            {
                while (reader.Read())
                {
                    metadata[reader.GetString(0)] = new RiskFactorItem
                    {
                        FactorCode = reader.GetString(0),
                        FactorName = reader.GetString(1),
                        Weight = reader.IsDBNull(2) ? 1m : reader.GetDecimal(2)
                    };
                }
            }

            return metadata;
        }

        private static RiskFactorItem BuildFactor(Dictionary<string, RiskFactorItem> metadata, string code, decimal value)
        {
            RiskFactorItem baseFactor;
            if (!metadata.TryGetValue(code, out baseFactor))
            {
                baseFactor = new RiskFactorItem
                {
                    FactorCode = code,
                    FactorName = code,
                    Weight = 1m
                };
            }

            var normalizedValue = decimal.Round(Clamp(value, 0m, 100m), 2, MidpointRounding.AwayFromZero);
            return new RiskFactorItem
            {
                FactorCode = baseFactor.FactorCode,
                FactorName = baseFactor.FactorName,
                Weight = baseFactor.Weight,
                Value = normalizedValue,
                ImpactScore = decimal.Round(normalizedValue * (baseFactor.Weight <= 0m ? 1m : baseFactor.Weight), 2, MidpointRounding.AwayFromZero)
            };
        }

        private static decimal GetModelValue(Dictionary<string, decimal> model, string key, decimal defaultValue)
        {
            decimal value;
            return model.TryGetValue(key, out value) ? value : defaultValue;
        }

        private static decimal NormalizeCreditScore(int creditScore)
        {
            return Clamp((creditScore - 300m) / 550m, 0m, 1m);
        }

        private static decimal NormalizeBalance(decimal balance, decimal requestedAmount)
        {
            if (requestedAmount <= 0m)
            {
                return 0.5m;
            }

            return Clamp(balance / requestedAmount, 0m, 1m);
        }

        private static decimal NormalizeTerm(int termMonths)
        {
            return Clamp(1m - (termMonths / 360m), 0m, 1m);
        }

        private static decimal NormalizeLoanAmount(decimal requestedAmount)
        {
            return Clamp(1m - (requestedAmount / 500000m), 0m, 1m);
        }

        private static string GetRating(decimal score)
        {
            if (score >= 85m) return "A";
            if (score >= 75m) return "B";
            if (score >= 65m) return "C";
            if (score >= 55m) return "D";
            if (score >= 45m) return "E";
            return "F";
        }

        private static decimal GetApprovalMultiplier(string rating)
        {
            switch (rating)
            {
                case "A": return 1.25m;
                case "B": return 1.10m;
                case "C": return 0.90m;
                case "D": return 0.70m;
                case "E": return 0.50m;
                default: return 0m;
            }
        }

        private static decimal Clamp(decimal value, decimal min, decimal max)
        {
            if (value < min) return min;
            if (value > max) return max;
            return value;
        }
    }
}

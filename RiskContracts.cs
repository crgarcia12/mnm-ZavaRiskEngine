using System;
using System.Collections.Generic;
using System.Runtime.Serialization;

namespace ZavaRiskEngine
{
    [DataContract]
    public class RiskScoreResponse
    {
        [DataMember] public int ApplicationId { get; set; }
        [DataMember] public int CustomerId { get; set; }
        [DataMember] public decimal RequestedAmount { get; set; }
        [DataMember] public decimal MaxApprovedAmount { get; set; }
        [DataMember] public decimal CalculatedScore { get; set; }
        [DataMember] public string RiskRating { get; set; }
        [DataMember] public DateTime EvaluatedAtUtc { get; set; }
    }

    [DataContract]
    public class RiskFactorItem
    {
        [DataMember] public string FactorCode { get; set; }
        [DataMember] public string FactorName { get; set; }
        [DataMember] public decimal Weight { get; set; }
        [DataMember] public decimal Value { get; set; }
        [DataMember] public decimal ImpactScore { get; set; }
    }

    [DataContract]
    public class RiskFactorsResponse
    {
        [DataMember] public int CustomerId { get; set; }
        [DataMember] public decimal OverallScore { get; set; }
        [DataMember] public List<RiskFactorItem> Factors { get; set; }
    }

    [DataContract]
    public class RiskModelParameter
    {
        [DataMember] public string Name { get; set; }
        [DataMember] public decimal Value { get; set; }
    }

    [DataContract]
    public class RiskModelUpdateRequest
    {
        [DataMember] public string UpdatedBy { get; set; }
        [DataMember] public List<RiskModelParameter> Parameters { get; set; }
    }

    [DataContract]
    public class RiskModelUpdateResponse
    {
        [DataMember] public bool Success { get; set; }
        [DataMember] public int UpdatedCount { get; set; }
        [DataMember] public string Message { get; set; }
        [DataMember] public DateTime UpdatedAtUtc { get; set; }
    }
}

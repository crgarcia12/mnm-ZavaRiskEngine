using System.ServiceModel;

namespace ZavaRiskEngine
{
    [ServiceContract]
    public interface IRiskEngineService
    {
        [OperationContract]
        RiskScoreResponse ScoreLoanApplication(int applicationId);

        [OperationContract]
        RiskFactorsResponse GetRiskFactors(int customerId);

        [OperationContract]
        RiskModelUpdateResponse UpdateRiskModel(RiskModelUpdateRequest modelParams);
    }
}

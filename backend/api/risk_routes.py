# Risk Prediction Agent API Routes
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
from datetime import datetime
import logging
from ..core.base import RiskPredictionRequest, RiskPredictionResponse
from ..agents.risk_prediction_agent import RiskPredictionAgent
from ..core.config import settings

router = APIRouter(prefix="/api/v1/risk", tags=["Risk Prediction"])
logger = logging.getLogger(__name__)

# Initialize risk prediction agent directly
risk_agent = RiskPredictionAgent()

@router.post("/predict", response_model=Dict[str, Any])
async def predict_amr_risk(request: RiskPredictionRequest):
    """Predict antimicrobial resistance risk for farm"""
    try:
        context = {"request_data": request.dict()}
        result = await risk_agent.execute("predict_amr_risk", context)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze-patterns", response_model=Dict[str, Any])
async def analyze_resistance_patterns(request_data: Dict[str, Any]):
    """Analyze resistance patterns using AI"""
    try:
        context = {"request_data": request_data}
        result = await risk_agent.execute("analyze_resistance_patterns", context)
        return result
    except Exception as e:
        logger.error(f"Error in resistance pattern analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/model-performance")
async def get_model_performance():
    """Get comprehensive model performance metrics"""
    try:
        performance = risk_agent.get_model_performance()
        return performance
    except Exception as e:
        logger.error(f"Error getting model performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/update-model", response_model=Dict[str, Any])
async def update_model_with_feedback(feedback_data: List[Dict[str, Any]]):
    """Update model with feedback data for continuous learning"""
    try:
        result = risk_agent.update_model_with_feedback(feedback_data)
        return result
    except Exception as e:
        logger.error(f"Error updating model: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/explain-prediction", response_model=Dict[str, Any])
async def explain_prediction(request_data: Dict[str, Any]):
    """Get detailed explanation of risk prediction"""
    try:
        import pandas as pd
        features_df = pd.DataFrame([request_data.get('features', {})])
        explanation = risk_agent.get_prediction_explanation(features_df)
        return explanation
    except Exception as e:
        logger.error(f"Error explaining prediction: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/feature-importance")
async def get_feature_importance():
    """Get current feature importance rankings"""
    try:
        # Generate sample data to get feature importance
        import pandas as pd
        sample_features = pd.DataFrame([{col: 0.5 for col in risk_agent.feature_columns}])
        risk_result = risk_agent._calculate_risk_score(sample_features)
        return {
            "feature_importance": risk_result.get("feature_importance", {}),
            "total_features": len(risk_agent.feature_columns),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting feature importance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def risk_health_check():
    """Health check for risk prediction agent"""
    try:
        return await risk_agent.health_check()
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))
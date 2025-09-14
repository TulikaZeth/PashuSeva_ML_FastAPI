# Risk Prediction Agent Implementation with AMR Model Integration
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import requests
import pickle
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import warnings
from ..core.base import BaseAgent, RiskPredictionRequest, RiskPredictionResponse
from ..core.config import settings

warnings.filterwarnings('ignore')

class RiskPredictionAgent(BaseAgent):
    """Antimicrobial Resistance Risk Prediction Agent"""
    
    def __init__(self):
        super().__init__(
            name="risk_prediction_agent",
            capabilities=[
                "amr_risk_prediction",
                "farm_level_assessment",
                "resistance_pattern_analysis",
                "treatment_outcome_prediction"
            ]
        )
        self.gemini_api_key = settings.gemini_api_key
        self.gemini_model = settings.gemini_model
        
        # Initialize ML models
        self.amr_model = None
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.feature_columns = []
        
        # Risk factors and weights
        self.risk_factors = {
            "antimicrobial_usage": {
                "high_frequency": 0.3,
                "broad_spectrum": 0.25,
                "prophylactic_use": 0.2,
                "subtherapeutic_use": 0.15
            },
            "farm_characteristics": {
                "high_animal_density": 0.2,
                "poor_hygiene": 0.25,
                "no_isolation_protocols": 0.15,
                "frequent_transport": 0.1
            },
            "historical_factors": {
                "previous_resistance": 0.4,
                "treatment_failures": 0.3,
                "outbreak_history": 0.2
            }
        }
        
        # AMR bacteria of concern
        self.target_bacteria = [
            "E. coli",
            "Salmonella",
            "Campylobacter",
            "Enterococcus",
            "Staphylococcus aureus"
        ]
        
        # Initialize model
        self._initialize_amr_model()
    
    async def activate(self) -> bool:
        """Activate the risk prediction agent"""
        try:
            # Load or train AMR model
            await self._load_or_train_model()
            
            self.is_active = True
            self.logger.info("Risk Prediction Agent activated successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to activate Risk Prediction Agent: {e}")
            return False
    
    def _initialize_amr_model(self):
        """Initialize enhanced AMR prediction model with better parameters"""
        # Enhanced RandomForest with optimized hyperparameters
        self.amr_model = RandomForestClassifier(
            n_estimators=200,  # Increased for better performance
            max_depth=15,      # Deeper trees for complex patterns
            min_samples_split=3,
            min_samples_leaf=1,
            max_features='sqrt',  # Optimal feature selection
            bootstrap=True,
            oob_score=True,    # Out-of-bag scoring
            class_weight='balanced',  # Handle imbalanced data
            random_state=42
        )
        
        # Initialize ensemble models for better predictions
        from sklearn.ensemble import GradientBoostingClassifier, ExtraTreesClassifier
        from sklearn.svm import SVC
        from sklearn.linear_model import LogisticRegression
        
        self.ensemble_models = {
            'gradient_boost': GradientBoostingClassifier(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=8,
                random_state=42
            ),
            'extra_trees': ExtraTreesClassifier(
                n_estimators=150,
                max_depth=12,
                random_state=42
            ),
            'svm': SVC(
                kernel='rbf',
                probability=True,
                random_state=42
            ),
            'logistic': LogisticRegression(
                random_state=42,
                max_iter=1000
            )
        }
        
        # Enhanced feature columns with more sophisticated indicators
        self.feature_columns = [
            # Antimicrobial usage features
            'total_antimicrobial_days',
            'broad_spectrum_usage',
            'prophylactic_usage_ratio',
            'treatment_duration_avg',
            'dosage_compliance_score',
            'antimicrobial_diversity_index',  # New: diversity of drugs used
            'treatment_frequency_score',      # New: frequency of treatments
            'critical_importance_usage',      # New: WHO critically important drugs
            
            # Farm characteristics
            'animal_density',
            'hygiene_score',
            'isolation_protocol_score',
            'ventilation_score',
            'feed_quality_score',
            'biosecurity_compliance_score',   # New: comprehensive biosecurity
            'waste_management_score',         # New: waste handling practices
            'water_quality_index',            # New: water quality metrics
            
            # Historical data
            'previous_resistance_events',
            'treatment_failure_rate',
            'mortality_rate',
            'morbidity_rate',
            'resistance_trend_slope',         # New: trend in resistance over time
            'outbreak_frequency',             # New: frequency of disease outbreaks
            'vet_consultation_frequency',     # New: veterinary involvement
            
            # Animal factors
            'avg_age_at_treatment',
            'stress_level_score',
            'immune_status_score',
            'genetic_susceptibility_score',   # New: breed-related resistance risk
            'vaccination_coverage',           # New: vaccination program effectiveness
            'nutritional_status_score',       # New: animal nutrition quality
            
            # Environmental factors
            'season_encoded',
            'temperature_avg',
            'humidity_avg',
            'air_quality_index',              # New: air quality metrics
            'pathogen_pressure_index',        # New: environmental pathogen load
            
            # Management factors
            'farm_size_category',             # New: farm size classification
            'production_system_type',         # New: intensive vs extensive
            'staff_training_score',           # New: staff competency
            'record_keeping_quality',         # New: documentation quality
            'technology_adoption_score'       # New: modern technology usage
        ]
    
    async def _call_gemini_for_analysis(self, prompt: str) -> str:
        """Call Gemini API for risk analysis"""
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.gemini_model}:generateContent"
            headers = {"x-goog-api-key": self.gemini_api_key, "Content-Type": "application/json"}
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code == 503:
                return "API temporarily unavailable"
            elif response.status_code != 200:
                return "Error in API response"
            
            return response.json()["candidates"][0]["content"]["parts"][0]["text"]
            
        except Exception as e:
            self.logger.error(f"Error calling Gemini API: {e}")
            return "Error in analysis"
    
    def _generate_synthetic_training_data(self, n_samples: int = 1000) -> Tuple[pd.DataFrame, np.ndarray]:
        """Generate synthetic training data for AMR model"""
        np.random.seed(42)
        
        data = {}
        
        # Generate features
        for feature in self.feature_columns:
            if 'ratio' in feature or 'score' in feature:
                # Scores and ratios (0-1)
                data[feature] = np.random.beta(2, 5, n_samples)
            elif 'rate' in feature:
                # Rates (0-1)
                data[feature] = np.random.beta(1.5, 8, n_samples)
            elif 'days' in feature or 'duration' in feature:
                # Days/duration (1-30)
                data[feature] = np.random.gamma(2, 3, n_samples)
            elif 'density' in feature:
                # Animal density (animals per m²)
                data[feature] = np.random.gamma(1, 2, n_samples)
            elif 'events' in feature:
                # Count data
                data[feature] = np.random.poisson(1.5, n_samples)
            elif 'age' in feature:
                # Age in months
                data[feature] = np.random.gamma(3, 4, n_samples)
            elif 'encoded' in feature:
                # Categorical encoded (0-3 for seasons)
                data[feature] = np.random.randint(0, 4, n_samples)
            elif 'temperature' in feature:
                # Temperature (°C)
                data[feature] = np.random.normal(20, 5, n_samples)
            elif 'humidity' in feature:
                # Humidity (%)
                data[feature] = np.random.normal(60, 15, n_samples)
            else:
                # Default: normalized values
                data[feature] = np.random.normal(0, 1, n_samples)
        
        df = pd.DataFrame(data)
        
        # Generate target variable (resistance risk: 0=low, 1=medium, 2=high)
        # Create logical relationships
        risk_score = (
            0.3 * df['total_antimicrobial_days'] +
            0.25 * df['broad_spectrum_usage'] +
            0.2 * df['previous_resistance_events'] +
            0.15 * df['treatment_failure_rate'] +
            0.1 * (1 - df['hygiene_score'])
        )
        
        # Normalize and convert to categories
        risk_score_norm = (risk_score - risk_score.min()) / (risk_score.max() - risk_score.min())
        
        # Define thresholds
        targets = np.where(risk_score_norm < 0.33, 0,
                          np.where(risk_score_norm < 0.67, 1, 2))
        
        return df, targets
    
    async def _load_or_train_model(self):
        """Load existing model or train new one"""
        model_path = "amr_model.pkl"
        scaler_path = "amr_scaler.pkl"
        
        try:
            # Try to load existing model
            if os.path.exists(model_path) and os.path.exists(scaler_path):
                self.amr_model = joblib.load(model_path)
                self.scaler = joblib.load(scaler_path)
                self.logger.info("Loaded existing AMR model")
            else:
                # Train new model
                await self._train_amr_model()
                
        except Exception as e:
            self.logger.warning(f"Error loading model, training new one: {e}")
            await self._train_amr_model()
    
    async def _train_amr_model(self):
        """Train enhanced AMR prediction model with ensemble methods"""
        try:
            # Generate training data
            X, y = self._generate_synthetic_training_data(3000)  # More training data
            
            # Advanced feature engineering
            X = self._engineer_features(X)
            
            # Split data with stratification
            from sklearn.model_selection import StratifiedKFold
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Train main Random Forest model
            self.amr_model.fit(X_train_scaled, y_train)
            
            # Train ensemble models
            for name, model in self.ensemble_models.items():
                try:
                    model.fit(X_train_scaled, y_train)
                    self.logger.info(f"Trained ensemble model: {name}")
                except Exception as e:
                    self.logger.warning(f"Failed to train {name}: {e}")
            
            # Cross-validation for robust evaluation
            cv_scores = self._cross_validate_model(X_train_scaled, y_train)
            
            # Evaluate main model
            y_pred = self.amr_model.predict(X_test_scaled)
            y_pred_proba = self.amr_model.predict_proba(X_test_scaled)
            
            # Calculate comprehensive metrics
            from sklearn.metrics import accuracy_score, precision_recall_fscore_support, roc_auc_score
            accuracy = accuracy_score(y_test, y_pred)
            precision, recall, f1, _ = precision_recall_fscore_support(y_test, y_pred, average='weighted')
            
            # Multi-class AUC
            try:
                auc_score = roc_auc_score(y_test, y_pred_proba, multi_class='ovr', average='weighted')
            except:
                auc_score = 0.0
            
            self.model_metrics = {
                'accuracy': accuracy,
                'precision': precision,
                'recall': recall,
                'f1_score': f1,
                'auc_score': auc_score,
                'cv_scores': cv_scores,
                'oob_score': getattr(self.amr_model, 'oob_score_', None)
            }
            
            self.logger.info(f"Enhanced AMR model trained - Accuracy: {accuracy:.3f}, F1: {f1:.3f}, AUC: {auc_score:.3f}")
            
            # Save enhanced model
            import joblib
            joblib.dump(self.amr_model, "amr_model_enhanced.pkl")
            joblib.dump(self.scaler, "amr_scaler_enhanced.pkl")
            joblib.dump(self.ensemble_models, "amr_ensemble_models.pkl")
            
        except Exception as e:
            self.logger.error(f"Error training enhanced AMR model: {e}")
    
    def _engineer_features(self, X):
        """Advanced feature engineering for better predictions"""
        X_enhanced = X.copy()
        
        # Interaction features
        X_enhanced['usage_density_interaction'] = X['total_antimicrobial_days'] * X['animal_density']
        X_enhanced['hygiene_resistance_interaction'] = X['hygiene_score'] * (1 - X['treatment_failure_rate'])
        X_enhanced['stress_immunity_interaction'] = X['stress_level_score'] * (1 - X['immune_status_score'])
        
        # Polynomial features for key metrics
        X_enhanced['antimicrobial_usage_squared'] = X['total_antimicrobial_days'] ** 2
        X_enhanced['resistance_events_log'] = np.log1p(X['previous_resistance_events'])
        
        # Risk composite scores
        X_enhanced['biosecurity_composite'] = (
            X['hygiene_score'] * 0.3 +
            X['isolation_protocol_score'] * 0.3 +
            X.get('biosecurity_compliance_score', 0.5) * 0.4
        )
        
        X_enhanced['antimicrobial_risk_composite'] = (
            X['broad_spectrum_usage'] * 0.4 +
            X['prophylactic_usage_ratio'] * 0.3 +
            X.get('critical_importance_usage', 0.2) * 0.3
        )
        
        return X_enhanced
    
    def _cross_validate_model(self, X, y):
        """Perform cross-validation for robust model evaluation"""
        from sklearn.model_selection import cross_val_score, StratifiedKFold
        
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        cv_scores = cross_val_score(self.amr_model, X, y, cv=cv, scoring='f1_weighted')
        
        return {
            'mean': cv_scores.mean(),
            'std': cv_scores.std(),
            'scores': cv_scores.tolist()
        }
    
    def _extract_features_from_request(self, request: RiskPredictionRequest) -> pd.DataFrame:
        """Extract features from request data"""
        features = {}
        
        # Initialize with defaults
        for feature in self.feature_columns:
            features[feature] = 0.0
        
        # Extract from farm data
        if request.farm_data:
            farm_data = request.farm_data
            
            # Animal density (animals per area)
            if "animal_count" in farm_data and "area_hectares" in farm_data:
                features['animal_density'] = farm_data["animal_count"] / max(farm_data["area_hectares"], 1)
            
            # Hygiene and management scores
            features['hygiene_score'] = farm_data.get("hygiene_score", 0.7)
            features['isolation_protocol_score'] = farm_data.get("isolation_protocols", 0.5)
            features['ventilation_score'] = farm_data.get("ventilation_quality", 0.6)
            features['feed_quality_score'] = farm_data.get("feed_quality", 0.8)
        
        # Extract from treatment history
        if request.treatment_history:
            treatments = request.treatment_history
            
            if treatments:
                # Calculate antimicrobial usage metrics
                total_days = sum(t.get("duration_days", 0) for t in treatments)
                features['total_antimicrobial_days'] = total_days
                
                # Broad spectrum usage ratio
                broad_spectrum_drugs = ["amoxicillin", "tetracycline", "florfenicol"]
                broad_spectrum_count = sum(1 for t in treatments 
                                         if any(drug in t.get("drug_name", "").lower() 
                                               for drug in broad_spectrum_drugs))
                features['broad_spectrum_usage'] = broad_spectrum_count / len(treatments)
                
                # Prophylactic usage
                prophylactic_count = sum(1 for t in treatments 
                                       if t.get("indication", "").lower() == "prophylactic")
                features['prophylactic_usage_ratio'] = prophylactic_count / len(treatments)
                
                # Average treatment duration
                features['treatment_duration_avg'] = total_days / len(treatments)
                
                # Dosage compliance (assume perfect compliance if not specified)
                features['dosage_compliance_score'] = 0.9
        
        # Extract from historical data
        if request.historical_data:
            hist_data = request.historical_data
            
            features['previous_resistance_events'] = hist_data.get("resistance_events", 0)
            features['treatment_failure_rate'] = hist_data.get("treatment_failures", 0) / max(hist_data.get("total_treatments", 1), 1)
            features['mortality_rate'] = hist_data.get("mortality_rate", 0.02)
            features['morbidity_rate'] = hist_data.get("morbidity_rate", 0.05)
        
        # Animal factors
        features['avg_age_at_treatment'] = 12  # Default 12 months
        features['stress_level_score'] = 0.3   # Low stress default
        features['immune_status_score'] = 0.7  # Good immune status default
        
        # Environmental factors (seasonal encoding)
        current_month = datetime.now().month
        features['season_encoded'] = (current_month - 1) // 3  # 0-3 for seasons
        features['temperature_avg'] = 20  # Default temperature
        features['humidity_avg'] = 60     # Default humidity
        
        return pd.DataFrame([features])
    
    def _calculate_risk_score(self, features: pd.DataFrame) -> Dict[str, Any]:
        """Calculate comprehensive risk score with ensemble predictions"""
        try:
            # Engineer features
            features_enhanced = self._engineer_features(features)
            
            # Ensure all required columns exist
            for col in self.feature_columns:
                if col not in features_enhanced.columns:
                    features_enhanced[col] = 0.0
            
            # Select only training features
            feature_subset = features_enhanced[self.feature_columns].fillna(0)
            
            # Scale features
            features_scaled = self.scaler.transform(feature_subset)
            
            # Main model predictions
            risk_category = self.amr_model.predict(features_scaled)[0]
            risk_probabilities = self.amr_model.predict_proba(features_scaled)[0]
            
            # Ensemble predictions for improved accuracy
            ensemble_predictions = {}
            ensemble_probabilities = {}
            
            if hasattr(self, 'ensemble_models'):
                for name, model in self.ensemble_models.items():
                    try:
                        pred = model.predict(features_scaled)[0]
                        prob = model.predict_proba(features_scaled)[0]
                        ensemble_predictions[name] = pred
                        ensemble_probabilities[name] = prob.tolist()
                    except Exception as e:
                        self.logger.warning(f"Ensemble model {name} prediction failed: {e}")
            
            # Weighted ensemble prediction
            ensemble_weights = {
                'random_forest': 0.4,
                'gradient_boost': 0.25,
                'extra_trees': 0.2,
                'svm': 0.1,
                'logistic': 0.05
            }
            
            weighted_probabilities = np.zeros(3)  # 3 classes
            total_weight = 0
            
            # Main model
            weighted_probabilities += risk_probabilities * ensemble_weights.get('random_forest', 0.4)
            total_weight += ensemble_weights.get('random_forest', 0.4)
            
            # Ensemble models
            for name, prob in ensemble_probabilities.items():
                weight = ensemble_weights.get(name, 0.1)
                weighted_probabilities += np.array(prob) * weight
                total_weight += weight
            
            if total_weight > 0:
                weighted_probabilities /= total_weight
                final_prediction = np.argmax(weighted_probabilities)
            else:
                final_prediction = risk_category
                weighted_probabilities = risk_probabilities
            
            # Convert to interpretable labels
            risk_labels = ["Low", "Medium", "High"]
            predicted_risk = risk_labels[final_prediction]
            
            # Enhanced component scores with new features
            component_scores = self._calculate_enhanced_component_scores(features_enhanced)
            
            # Overall risk score (0-100) with ensemble weighting
            overall_score = (
                component_scores['antimicrobial_usage'] * 35 +
                component_scores['farm_management'] * 25 +
                component_scores['historical_risk'] * 20 +
                component_scores['biosecurity'] * 15 +
                component_scores['environmental_factors'] * 5
            )
            
            # Confidence score based on ensemble agreement
            confidence_score = self._calculate_confidence_score(ensemble_predictions, final_prediction)
            
            # Feature importance
            feature_importance = self._get_enhanced_feature_importance(features_enhanced)
            
            return {
                "overall_risk_score": round(overall_score, 2),
                "risk_category": predicted_risk,
                "confidence_score": round(confidence_score, 3),
                "risk_probabilities": {
                    "low": round(weighted_probabilities[0], 3),
                    "medium": round(weighted_probabilities[1], 3),
                    "high": round(weighted_probabilities[2], 3)
                },
                "component_scores": {k: round(v, 3) for k, v in component_scores.items()},
                "feature_importance": feature_importance,
                "ensemble_predictions": ensemble_predictions,
                "model_confidence": {
                    "prediction_stability": confidence_score,
                    "feature_coverage": len(feature_importance) / len(self.feature_columns)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating enhanced risk score: {e}")
            return {
                "overall_risk_score": 50.0,
                "risk_category": "Medium",
                "confidence_score": 0.5,
                "error": str(e)
            }
    
    def _calculate_enhanced_component_scores(self, features: pd.DataFrame) -> Dict[str, float]:
        """Calculate enhanced component scores with new features"""
        scores = {}
        
        # Antimicrobial usage score (enhanced)
        amu_components = [
            features.get('total_antimicrobial_days', 0) / 30 * 0.25,
            features.get('broad_spectrum_usage', 0) * 0.25,
            features.get('prophylactic_usage_ratio', 0) * 0.2,
            features.get('critical_importance_usage', 0) * 0.15,
            features.get('antimicrobial_diversity_index', 0) * 0.15
        ]
        scores['antimicrobial_usage'] = min(1.0, sum(amu_components))
        
        # Farm management score (enhanced)
        farm_components = [
            (1 - features.get('hygiene_score', 0.7)) * 0.25,
            (1 - features.get('isolation_protocol_score', 0.5)) * 0.2,
            features.get('animal_density', 1) / 10 * 0.2,
            (1 - features.get('biosecurity_compliance_score', 0.6)) * 0.2,
            (1 - features.get('waste_management_score', 0.7)) * 0.15
        ]
        scores['farm_management'] = min(1.0, sum(farm_components))
        
        # Historical risk score (enhanced)
        hist_components = [
            features.get('previous_resistance_events', 0) / 10 * 0.3,
            features.get('treatment_failure_rate', 0) * 0.25,
            features.get('resistance_trend_slope', 0) * 0.25,
            features.get('outbreak_frequency', 0) / 5 * 0.2
        ]
        scores['historical_risk'] = min(1.0, sum(hist_components))
        
        # Biosecurity score (new)
        biosecurity_components = [
            (1 - features.get('biosecurity_compliance_score', 0.6)) * 0.4,
            (1 - features.get('vet_consultation_frequency', 0.5)) * 0.3,
            (1 - features.get('vaccination_coverage', 0.8)) * 0.3
        ]
        scores['biosecurity'] = min(1.0, sum(biosecurity_components))
        
        # Environmental factors score (new)
        env_components = [
            features.get('pathogen_pressure_index', 0.3) * 0.4,
            (1 - features.get('air_quality_index', 0.7)) * 0.3,
            (1 - features.get('water_quality_index', 0.8)) * 0.3
        ]
        scores['environmental_factors'] = min(1.0, sum(env_components))
        
        return scores
    
    def _calculate_confidence_score(self, ensemble_predictions: Dict, final_prediction: int) -> float:
        """Calculate confidence score based on ensemble agreement"""
        if not ensemble_predictions:
            return 0.7  # Default confidence for single model
        
        agreements = sum(1 for pred in ensemble_predictions.values() if pred == final_prediction)
        total_models = len(ensemble_predictions) + 1  # +1 for main model
        
        confidence = agreements / total_models
        return confidence
    
    def _get_enhanced_feature_importance(self, features: pd.DataFrame) -> Dict[str, float]:
        """Get enhanced feature importance with ensemble averaging"""
        importance_dict = {}
        
        # Main model importance
        if hasattr(self.amr_model, 'feature_importances_'):
            main_importance = self.amr_model.feature_importances_
            
            for i, feature in enumerate(self.feature_columns[:len(main_importance)]):
                importance_dict[feature] = main_importance[i] * 0.5  # Weight main model
        
        # Ensemble model importance (if available)
        if hasattr(self, 'ensemble_models'):
            for name, model in self.ensemble_models.items():
                if hasattr(model, 'feature_importances_'):
                    model_importance = model.feature_importances_
                    weight = 0.5 / len(self.ensemble_models)  # Distribute remaining weight
                    
                    for i, feature in enumerate(self.feature_columns[:len(model_importance)]):
                        importance_dict[feature] = importance_dict.get(feature, 0) + model_importance[i] * weight
        
        # Sort by importance
        sorted_importance = dict(sorted(importance_dict.items(), 
                                      key=lambda x: x[1], reverse=True)[:15])
        return {k: round(v, 4) for k, v in sorted_importance.items()}
    
    def _get_feature_importance(self, features: pd.DataFrame) -> Dict[str, float]:
        """Get feature importance for this prediction"""
        if hasattr(self.amr_model, 'feature_importances_'):
            importance_dict = {}
            for i, feature in enumerate(self.feature_columns):
                if i < len(self.amr_model.feature_importances_):
                    importance_dict[feature] = round(self.amr_model.feature_importances_[i], 3)
            
            # Sort by importance
            sorted_importance = dict(sorted(importance_dict.items(), 
                                          key=lambda x: x[1], reverse=True)[:10])
            return sorted_importance
        
        return {}
    
    def _generate_recommendations(self, risk_analysis: Dict) -> List[str]:
        """Generate risk mitigation recommendations"""
        recommendations = []
        
        risk_score = risk_analysis["overall_risk_score"]
        component_scores = risk_analysis.get("component_scores", {})
        
        # High-level recommendations based on overall risk
        if risk_score > 70:
            recommendations.append("URGENT: Implement immediate AMR mitigation strategies")
            recommendations.append("Consider temporary antimicrobial usage restrictions")
            recommendations.append("Conduct comprehensive farm biosecurity audit")
        elif risk_score > 40:
            recommendations.append("Moderate risk detected - enhance monitoring protocols")
            recommendations.append("Review and optimize antimicrobial usage policies")
        else:
            recommendations.append("Low risk - maintain current best practices")
            recommendations.append("Continue routine surveillance and monitoring")
        
        # Component-specific recommendations
        if component_scores.get("antimicrobial_usage", 0) > 0.6:
            recommendations.extend([
                "Reduce prophylactic antimicrobial usage",
                "Implement antimicrobial stewardship program",
                "Consider narrow-spectrum alternatives",
                "Ensure proper dosing and treatment duration"
            ])
        
        if component_scores.get("farm_management", 0) > 0.6:
            recommendations.extend([
                "Improve farm hygiene and sanitation protocols",
                "Enhance isolation procedures for sick animals",
                "Reduce animal density if possible",
                "Improve ventilation and housing conditions"
            ])
        
        if component_scores.get("historical_risk", 0) > 0.6:
            recommendations.extend([
                "Investigate previous resistance patterns",
                "Review treatment failure cases",
                "Implement enhanced surveillance programs",
                "Consider changing antimicrobial protocols"
            ])
        
        # General best practices
        recommendations.extend([
            "Regular antimicrobial susceptibility testing",
            "Staff training on proper antimicrobial use",
            "Maintain detailed treatment records",
            "Consult with veterinary professionals regularly"
        ])
        
        return recommendations[:10]  # Limit to top 10 recommendations
    
    async def analyze_animal_risk(self, animal_id: str, treatment_history: List[Dict], animal_characteristics: Dict) -> Dict[str, Any]:
        """Analyze AMR risk for a specific animal based on treatment history"""
        try:
            risk_summary = {
                "animal_id": animal_id,
                "risk_score": 0.0,
                "risk_category": "low",
                "risk_factors": {},
                "treatment_analysis": {},
                "recommendations": []
            }
            
            # Analyze treatment history
            antimicrobial_treatments = []
            critical_drugs_used = []
            total_treatment_days = 0
            
            for treatment in treatment_history:
                # Check if it's a prescription with medicines
                if "medicines" in treatment:
                    for medicine in treatment.get("medicines", []):
                        med_name = medicine.get("name", "").lower()
                        if any(drug in med_name for drug in ["penicillin", "amoxicillin", "tetracycline", "enrofloxacin"]):
                            antimicrobial_treatments.append({
                                "drug": medicine.get("name"),
                                "dosage": medicine.get("dosage"),
                                "duration": medicine.get("duration"),
                                "type": "prescription"
                            })
                            
                            # Check for critical drugs
                            if any(critical in med_name for critical in ["enrofloxacin", "ciprofloxacin", "ceftiofur"]):
                                critical_drugs_used.append(medicine.get("name"))
                
                # Check if it's a treatment record
                elif "medication" in treatment:
                    med_name = treatment.get("medication", "").lower()
                    if any(drug in med_name for drug in ["penicillin", "amoxicillin", "tetracycline", "enrofloxacin"]):
                        antimicrobial_treatments.append({
                            "drug": treatment.get("medication"),
                            "type": "treatment",
                            "status": treatment.get("status", "")
                        })
            
            # Calculate risk factors
            risk_factors = {
                "treatment_frequency": min(len(antimicrobial_treatments) / 10.0, 1.0),  # Normalize to 0-1
                "critical_drug_usage": min(len(critical_drugs_used) / 3.0, 1.0),
                "treatment_diversity": min(len(set(t.get("drug", "") for t in antimicrobial_treatments)) / 5.0, 1.0)
            }
            
            # Calculate overall risk score
            base_score = (
                risk_factors["treatment_frequency"] * 0.4 +
                risk_factors["critical_drug_usage"] * 0.4 +
                risk_factors["treatment_diversity"] * 0.2
            )
            
            # Adjust based on animal characteristics
            breed_modifier = 1.0
            if animal_characteristics.get("breed", "").lower() in ["dairy", "holstein"]:
                breed_modifier = 1.1  # Slightly higher risk for dairy cattle
            
            final_risk_score = min(base_score * breed_modifier, 1.0)
            
            # Determine risk category
            if final_risk_score < 0.3:
                risk_category = "low"
            elif final_risk_score < 0.6:
                risk_category = "moderate"
            else:
                risk_category = "high"
            
            # Generate recommendations based on risk level
            recommendations = []
            if risk_category == "low":
                recommendations.extend([
                    "Continue current antimicrobial stewardship practices",
                    "Monitor for any changes in treatment patterns",
                    "Maintain accurate treatment records"
                ])
            elif risk_category == "moderate":
                recommendations.extend([
                    "Review antimicrobial usage patterns",
                    "Consider implementing rotation protocols",
                    "Increase monitoring for treatment failures",
                    "Consult with veterinarian about stewardship programs"
                ])
            else:  # high risk
                recommendations.extend([
                    "Immediate review of antimicrobial protocols required",
                    "Implement strict stewardship guidelines",
                    "Conduct antimicrobial susceptibility testing",
                    "Consider alternative treatment approaches",
                    "Increase surveillance for resistant organisms"
                ])
            
            # Add specific warnings for critical drugs
            if critical_drugs_used:
                recommendations.append(f"Critical antimicrobials detected: {', '.join(critical_drugs_used)} - require special monitoring")
            
            risk_summary.update({
                "risk_score": round(final_risk_score, 3),
                "risk_category": risk_category,
                "risk_factors": risk_factors,
                "treatment_analysis": {
                    "total_antimicrobial_treatments": len(antimicrobial_treatments),
                    "critical_drugs_used": critical_drugs_used,
                    "drug_diversity": len(set(t.get("drug", "") for t in antimicrobial_treatments))
                },
                "recommendations": recommendations
            })
            
            return risk_summary
            
        except Exception as e:
            self.logger.error(f"Error analyzing animal AMR risk: {e}")
            return {"error": f"Failed to analyze AMR risk: {str(e)}"}
    
    async def execute(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute risk prediction task"""
        try:
            if task == "predict_amr_risk":
                request_data = context.get("request_data")
                if not request_data:
                    # Try animal-centric format
                    return await self.analyze_animal_risk(
                        context.get("animal_id", ""),
                        context.get("treatment_history", []),
                        context.get("animal_characteristics", {})
                    )
                
                request = RiskPredictionRequest(**request_data)
                
                # Extract features from request
                features = self._extract_features_from_request(request)
                
                # Calculate risk score
                risk_analysis = self._calculate_risk_score(features)
                
                # Generate recommendations
                recommendations = self._generate_recommendations(risk_analysis)
                
                return RiskPredictionResponse(
                    success=True,
                    message="AMR risk prediction completed",
                    service_name=self.name,
                    timestamp=datetime.now().isoformat(),
                    farm_id=request.farm_id,
                    risk_score=risk_analysis["overall_risk_score"],
                    risk_category=risk_analysis["risk_category"],
                    risk_factors=risk_analysis.get("component_scores", {}),
                    recommendations=recommendations
                ).dict()
            
            elif task == "analyze_resistance_patterns":
                # Use Gemini for resistance pattern analysis
                request_data = context.get("request_data", {})
                
                prompt = f"""
                Analyze antimicrobial resistance patterns for farm:
                
                Farm Data: {request_data.get('farm_data', {})}
                Treatment History: {request_data.get('treatment_history', [])}
                Historical Data: {request_data.get('historical_data', {})}
                
                Provide analysis including:
                1. Resistance trend identification
                2. Bacterial species of concern
                3. Antimicrobial efficacy patterns
                4. Risk factor interactions
                5. Predictive insights for future resistance
                
                Focus on actionable insights for farm management.
                """
                
                analysis = await self._call_gemini_for_analysis(prompt)
                
                return {
                    "resistance_analysis": analysis,
                    "timestamp": datetime.now().isoformat()
                }
            
            else:
                return {"error": f"Unknown task: {task}"}
                
        except Exception as e:
            self.logger.error(f"Error executing task {task}: {e}")
            return {"error": str(e)}
    
    async def get_capabilities(self) -> List[str]:
        """Return agent capabilities"""
        return self.capabilities
    
    def get_model_performance(self) -> Dict[str, Any]:
        """Get comprehensive model performance metrics"""
        if self.amr_model is None:
            return {"error": "Model not trained"}
        
        performance_data = {
            "model_type": "Enhanced RandomForestClassifier with Ensemble",
            "n_features": len(self.feature_columns),
            "classes": ["Low Risk", "Medium Risk", "High Risk"],
            "ensemble_models": list(getattr(self, 'ensemble_models', {}).keys())
        }
        
        # Add training metrics if available
        if hasattr(self, 'model_metrics'):
            performance_data.update(self.model_metrics)
        
        # Generate test data for current performance evaluation
        try:
            X_test, y_test = self._generate_synthetic_training_data(300)
            X_test_enhanced = self._engineer_features(X_test)
            
            # Ensure feature alignment
            feature_subset = X_test_enhanced[self.feature_columns].fillna(0)
            X_test_scaled = self.scaler.transform(feature_subset)
            
            y_pred = self.amr_model.predict(X_test_scaled)
            accuracy = (y_pred == y_test).mean()
            
            performance_data.update({
                "current_accuracy": round(accuracy, 3),
                "feature_coverage": len(self.feature_columns),
                "last_evaluation": datetime.now().isoformat()
            })
            
        except Exception as e:
            performance_data["evaluation_error"] = str(e)
        
        return performance_data
    
    def update_model_with_feedback(self, feedback_data: List[Dict]) -> Dict[str, Any]:
        """Update model with new feedback data for continuous learning"""
        try:
            if not feedback_data:
                return {"error": "No feedback data provided"}
            
            # Process feedback data
            feedback_df = pd.DataFrame(feedback_data)
            
            # Extract features and targets
            X_feedback = self._extract_features_from_feedback(feedback_df)
            y_feedback = feedback_df.get('actual_risk_level', []).tolist()
            
            if len(X_feedback) == 0 or len(y_feedback) == 0:
                return {"error": "Invalid feedback data format"}
            
            # Engineer features
            X_feedback_enhanced = self._engineer_features(X_feedback)
            feature_subset = X_feedback_enhanced[self.feature_columns].fillna(0)
            X_feedback_scaled = self.scaler.transform(feature_subset)
            
            # Incremental learning (partial_fit for applicable models)
            models_updated = []
            
            # Update ensemble models that support incremental learning
            if hasattr(self, 'ensemble_models'):
                for name, model in self.ensemble_models.items():
                    if hasattr(model, 'partial_fit'):
                        try:
                            model.partial_fit(X_feedback_scaled, y_feedback)
                            models_updated.append(name)
                        except Exception as e:
                            self.logger.warning(f"Failed to update {name}: {e}")
            
            # For Random Forest, retrain periodically with accumulated data
            if len(feedback_data) > 50:  # Retrain threshold
                try:
                    self._retrain_with_feedback(X_feedback_scaled, y_feedback)
                    models_updated.append("random_forest")
                except Exception as e:
                    self.logger.error(f"Error in model retraining: {e}")
            
            return {
                "success": True,
                "models_updated": models_updated,
                "feedback_samples_processed": len(feedback_data),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error updating model with feedback: {e}")
            return {"error": str(e)}
    
    def _extract_features_from_feedback(self, feedback_df: pd.DataFrame) -> pd.DataFrame:
        """Extract features from feedback data"""
        # Initialize feature dataframe
        features = pd.DataFrame()
        
        # Map feedback columns to feature columns
        feature_mapping = {
            'antimicrobial_days': 'total_antimicrobial_days',
            'broad_spectrum_ratio': 'broad_spectrum_usage',
            'prophylactic_ratio': 'prophylactic_usage_ratio',
            'animal_density': 'animal_density',
            'hygiene_score': 'hygiene_score',
            'resistance_events': 'previous_resistance_events',
            'treatment_failures': 'treatment_failure_rate'
        }
        
        for feedback_col, feature_col in feature_mapping.items():
            if feedback_col in feedback_df.columns:
                features[feature_col] = feedback_df[feedback_col]
        
        # Fill missing features with defaults
        for col in self.feature_columns:
            if col not in features.columns:
                features[col] = self._get_default_feature_value(col)
        
        return features
    
    def _get_default_feature_value(self, feature_name: str) -> float:
        """Get default value for a feature"""
        defaults = {
            'total_antimicrobial_days': 5.0,
            'broad_spectrum_usage': 0.3,
            'prophylactic_usage_ratio': 0.2,
            'animal_density': 2.0,
            'hygiene_score': 0.7,
            'isolation_protocol_score': 0.6,
            'previous_resistance_events': 1.0,
            'treatment_failure_rate': 0.1,
            'mortality_rate': 0.02,
            'season_encoded': 1.0,
            'temperature_avg': 20.0,
            'humidity_avg': 60.0
        }
        return defaults.get(feature_name, 0.5)
    
    def _retrain_with_feedback(self, X_feedback: np.ndarray, y_feedback: List[int]):
        """Retrain model incorporating feedback data"""
        try:
            # Generate base training data
            X_base, y_base = self._generate_synthetic_training_data(2000)
            X_base_enhanced = self._engineer_features(X_base)
            feature_subset = X_base_enhanced[self.feature_columns].fillna(0)
            X_base_scaled = self.scaler.transform(feature_subset)
            
            # Combine base data with feedback
            X_combined = np.vstack([X_base_scaled, X_feedback])
            y_combined = np.hstack([y_base, y_feedback])
            
            # Retrain main model
            self.amr_model.fit(X_combined, y_combined)
            
            # Save updated model
            import joblib
            joblib.dump(self.amr_model, "amr_model_updated.pkl")
            
            self.logger.info(f"Model retrained with {len(y_feedback)} feedback samples")
            
        except Exception as e:
            self.logger.error(f"Error retraining model: {e}")
    
    def get_prediction_explanation(self, features: pd.DataFrame) -> Dict[str, Any]:
        """Get detailed explanation of prediction using SHAP-like analysis"""
        try:
            # Calculate risk score
            risk_result = self._calculate_risk_score(features)
            
            # Feature importance
            feature_importance = risk_result.get('feature_importance', {})
            
            # Top contributing factors
            top_factors = list(feature_importance.items())[:5]
            
            # Risk factors explanation
            explanations = []
            for factor, importance in top_factors:
                feature_value = features.get(factor, [0]).iloc[0] if len(features) > 0 else 0
                
                explanation = self._get_factor_explanation(factor, feature_value, importance)
                explanations.append(explanation)
            
            return {
                "prediction": risk_result['risk_category'],
                "confidence": risk_result.get('confidence_score', 0.5),
                "overall_score": risk_result['overall_risk_score'],
                "key_explanations": explanations,
                "component_breakdown": risk_result.get('component_scores', {}),
                "model_certainty": risk_result.get('model_confidence', {})
            }
            
        except Exception as e:
            self.logger.error(f"Error generating prediction explanation: {e}")
            return {"error": str(e)}
    
    def _get_factor_explanation(self, factor: str, value: float, importance: float) -> Dict[str, Any]:
        """Get human-readable explanation for a factor"""
        explanations = {
            'total_antimicrobial_days': {
                'name': 'Antimicrobial Usage Days',
                'description': f'Farm used antimicrobials for {value:.1f} days on average',
                'impact': 'high' if value > 15 else 'medium' if value > 7 else 'low'
            },
            'broad_spectrum_usage': {
                'name': 'Broad Spectrum Drug Usage',
                'description': f'{value*100:.1f}% of treatments used broad-spectrum antimicrobials',
                'impact': 'high' if value > 0.5 else 'medium' if value > 0.3 else 'low'
            },
            'previous_resistance_events': {
                'name': 'Historical Resistance',
                'description': f'{value:.0f} previous antimicrobial resistance events recorded',
                'impact': 'high' if value > 3 else 'medium' if value > 1 else 'low'
            },
            'hygiene_score': {
                'name': 'Farm Hygiene Standards',
                'description': f'Hygiene score: {value*100:.0f}% (higher is better)',
                'impact': 'low' if value > 0.8 else 'medium' if value > 0.6 else 'high'
            }
        }
        
        default_explanation = {
            'name': factor.replace('_', ' ').title(),
            'description': f'Value: {value:.2f}',
            'impact': 'medium'
        }
        
        explanation = explanations.get(factor, default_explanation)
        explanation['importance_score'] = round(importance, 3)
        
        return explanation
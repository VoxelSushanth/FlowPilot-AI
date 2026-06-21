"""
Retailer/Customer management models with credit and risk scoring.
"""

from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from sqlalchemy import String, Numeric, ForeignKey, Integer, Boolean, DateTime, Text, Enum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from ..core.base import BaseModel


class RetailerStatus(enum.Enum):
    """Retailer account status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    BLOCKED = "blocked"
    PROSPECT = "prospect"


class RiskLevel(enum.Enum):
    """Credit risk classification."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class Retailer(BaseModel):
    """
    Customer/Retailer profile.
    
    Central entity for B2B customer management with credit tracking.
    """
    __tablename__ = "retailers"
    
    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id"), nullable=False, index=True
    )
    
    # Identification
    retailer_code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    gst_number: Mapped[Optional[str]] = mapped_column(String(15), nullable=True)
    pan_number: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    
    # Business details
    business_name: Mapped[str] = mapped_column(String(255), nullable=False)
    proprietor_name: Mapped[str] = mapped_column(String(255), nullable=False)
    business_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # retail, wholesale, institutional
    
    # Contact
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone_primary: Mapped[str] = mapped_column(String(20), nullable=False)
    phone_secondary: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # Address
    address_line1: Mapped[str] = mapped_column(String(500), nullable=False)
    address_line2: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(100), nullable=False)
    pincode: Mapped[str] = mapped_column(String(10), nullable=False)
    
    # Geo-location (for route optimization)
    latitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 8), nullable=True)
    longitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(11, 8), nullable=True)
    
    # Status
    status: Mapped[RetailerStatus] = mapped_column(Enum(RetailerStatus), default=RetailerStatus.PROSPECT, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Classification
    tier: Mapped[str] = mapped_column(String(20), default="standard", nullable=False)  # platinum, gold, silver, standard
    segment: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # modern_trade, general_trade, horeca
    
    # Sales rep assignment
    sales_rep_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    route_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Delivery route
    
    # Tags for segmentation
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    
    # Metadata
    source: Mapped[str] = mapped_column(String(50), default="manual", nullable=False)
    reference_retailer_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # For hierarchies
    
    # Relationships
    sales_rep = relationship("User")
    credit_limits = relationship("CreditLimit", back_populates="retailer", lazy="select")
    risk_scores = relationship("RiskScore", back_populates="retailer", lazy="select")
    
    @property
    def current_credit_limit(self) -> Optional[Decimal]:
        """Get the currently active credit limit."""
        active_limits = [cl for cl in self.credit_limits if cl.is_active]
        if not active_limits:
            return None
        # Return the most recent
        return max(active_limits, key=lambda x: x.effective_from).limit_amount
    
    @property
    def current_risk_level(self) -> Optional[RiskLevel]:
        """Get the current risk level."""
        active_scores = [rs for rs in self.risk_scores if rs.is_active]
        if not active_scores:
            return None
        return max(active_scores, key=lambda x: x.calculated_at).risk_level


class CreditLimit(BaseModel):
    """
    Credit limit configuration for a retailer.
    
    Supports multiple limits with validity periods for audit trail.
    """
    __tablename__ = "credit_limits"
    
    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id"), nullable=False, index=True
    )
    
    retailer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("retailers.id"), nullable=False, index=True
    )
    
    # Limit amount
    limit_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    
    # Validity period
    effective_from: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    effective_until: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Approval
    approved_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    approval_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    approval_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Relationships
    retailer = relationship("Retailer", back_populates="credit_limits")
    approver = relationship("User")
    
    @property
    def is_expired(self) -> bool:
        """Check if the credit limit has expired."""
        if self.effective_until is None:
            return False
        return datetime.utcnow() > self.effective_until


class RiskScore(BaseModel):
    """
    AI-generated risk score for credit assessment.
    
    Updated periodically by the forecasting/risk ML model.
    """
    __tablename__ = "risk_scores"
    
    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id"), nullable=False, index=True
    )
    
    retailer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("retailers.id"), nullable=False, index=True
    )
    
    # Score details
    score_value: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)  # 0-100 scale
    risk_level: Mapped[RiskLevel] = mapped_column(Enum(RiskLevel), nullable=False)
    
    # Model context
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)
    calculated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    
    # Contributing factors (stored as JSON for flexibility)
    # Example: {"payment_delay_avg": 5.2, "order_frequency": 12, "bad_debt_history": false}
    contributing_factors: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Prediction confidence
    confidence_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Relationships
    retailer = relationship("Retailer", back_populates="risk_scores")
    
    @property
    def recommended_action(self) -> str:
        """Get recommended action based on risk level."""
        actions = {
            RiskLevel.LOW: "Approve standard credit terms",
            RiskLevel.MEDIUM: "Review before approving large orders",
            RiskLevel.HIGH: "Require advance payment or reduced credit",
            RiskLevel.VERY_HIGH: "Cash only, no credit",
        }
        return actions.get(self.risk_level, "Manual review required")

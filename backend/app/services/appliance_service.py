from datetime import date
from typing import List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.appliance import Appliance
from app.schemas.appliance import ApplianceCreate, ApplianceUpdate


class ApplianceService:
    @staticmethod
    def get_active_appliances(db: Session) -> List[Appliance]:
        return db.query(Appliance).filter(Appliance.is_active == True).order_by(Appliance.id.desc()).all()

    @staticmethod
    def get_appliance_by_id(db: Session, appliance_id: int) -> Appliance:
        appliance = db.query(Appliance).filter(Appliance.id == appliance_id).first()
        if not appliance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Appliance with id {appliance_id} not found"
            )
        return appliance

    @staticmethod
    def create_appliance(db: Session, appliance_in: ApplianceCreate) -> Appliance:
        # Additional business logic check for dates
        if appliance_in.purchase_date and appliance_in.purchase_date > date.today():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Purchase date cannot be in the future"
            )
        if (
            appliance_in.purchase_date
            and appliance_in.warranty_expiry
            and appliance_in.warranty_expiry < appliance_in.purchase_date
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Warranty expiry cannot be earlier than purchase date"
            )

        appliance = Appliance(
            name=appliance_in.name,
            brand=appliance_in.brand,
            model_number=appliance_in.model_number,
            category=appliance_in.category,
            purchase_date=appliance_in.purchase_date,
            warranty_expiry=appliance_in.warranty_expiry,
            location=appliance_in.location,
            notes=appliance_in.notes,
            is_active=appliance_in.is_active,
        )
        db.add(appliance)
        db.commit()
        db.refresh(appliance)
        return appliance

    @staticmethod
    def update_appliance(db: Session, appliance_id: int, appliance_in: ApplianceUpdate) -> Appliance:
        appliance = ApplianceService.get_appliance_by_id(db, appliance_id)

        update_data = appliance_in.model_dump(exclude_unset=True)

        target_purchase_date = update_data.get("purchase_date", appliance.purchase_date)
        target_warranty_expiry = update_data.get("warranty_expiry", appliance.warranty_expiry)

        if target_purchase_date and target_purchase_date > date.today():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Purchase date cannot be in the future"
            )
        if target_purchase_date and target_warranty_expiry and target_warranty_expiry < target_purchase_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Warranty expiry cannot be earlier than purchase date"
            )

        for field, value in update_data.items():
            setattr(appliance, field, value)

        db.commit()
        db.refresh(appliance)
        return appliance

    @staticmethod
    def soft_delete_appliance(db: Session, appliance_id: int) -> Appliance:
        appliance = ApplianceService.get_appliance_by_id(db, appliance_id)
        appliance.is_active = False
        db.commit()
        db.refresh(appliance)
        return appliance

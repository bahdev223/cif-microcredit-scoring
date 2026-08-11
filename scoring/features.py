def build_features(client, application):
    installment = application.estimated_installment
    repayment_capacity = client.monthly_income - client.monthly_expenses
    return {
        "repayment_capacity": repayment_capacity,
        "installment": installment,
        "capacity_ratio": repayment_capacity / installment if installment else 0,
        "business_age_months": client.business_age_months,
        "late_payments": client.late_payments,
        "tontine_regularity": client.tontine_regularity,
    }

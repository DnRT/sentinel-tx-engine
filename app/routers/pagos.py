from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .. import schemas, database, logic

router = APIRouter(
    prefix="/api/v1",
    tags=["Pagos"]
)

@router.post("/validar_pago", response_model=schemas.TransaccionResponse)
def validar_pago(request: schemas.TransaccionRequest, db: Session = Depends(database.get_db)):
    try:
        resultado = logic.evaluar_transaccion(db, request)
        return schemas.TransaccionResponse(
            estado=resultado.estado,
            razon_estado=resultado.razon_estado,
            monto=resultado.monto,
            score_riesgo_calculado=resultado.score_riesgo_calculado,
            cuenta_destino=resultado.cuenta_destino
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno procesando la transacción: {str(e)}"
        )

DELETE FROM TITULACION where id not in (
    select titulacion from PUESTO_TITULACION
)
and txt='¿?'
;
DELETE FROM CUERPO where id not in (
    select cuerpo from PUESTO_CUERPO
)
and txt='¿?'
;
DELETE FROM OBSERVACION where id not in (
    select observacion from PUESTO_OBSERVACION
)
and txt='¿?'
;
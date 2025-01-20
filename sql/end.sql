DELETE FROM TITULACION where txt='¿?' and id not in (
    select titulacion from PUESTO_TITULACION
);
DELETE FROM CUERPO where txt='¿?' and id not in (
    select cuerpo from PUESTO_CUERPO
);
DELETE FROM OBSERVACION where txt='¿?' and id not in (
    select observacion from PUESTO_OBSERVACION
);
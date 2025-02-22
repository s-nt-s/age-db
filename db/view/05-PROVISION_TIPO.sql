select distinct
    provision,
    tipo
from
    puesto
where
    tipo is not null or
    provision is not null
;
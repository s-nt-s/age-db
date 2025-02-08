select distinct
    g.grupo,
    p.nivel
from
    puesto_grupo g 
    join puesto p on 
        p.id=g.puesto
order by
    g.grupo,
    p.nivel;
select
    n.id,
    n.destino,
    min(p.especifico) min_especifico,
    max(p.especifico) max_especifico
from
    nivel n
    left join puesto p on 
        n.id=p.nivel
group by
    n.id,
    n.destino
order by
    n.id;
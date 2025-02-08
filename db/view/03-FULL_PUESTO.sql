with
g as (
	select puesto id, string_agg(grupo, E'\t') AS val
	from puesto_grupo
	group by puesto
),
o as (
	select puesto id, string_agg(observacion, E'\t') AS val
	from puesto_observacion
	group by puesto
),
c as (
	select puesto id, string_agg(cuerpo, E'\t') AS val
	from puesto_cuerpo
	group by puesto
),
t as (
	select puesto id, string_agg(titulacion, E'\t') AS val
	from puesto_titulacion
	group by puesto
)
select
	p.id,
	p.vacante,
	coalesce(p.localidad, unidad.localidad) localidad,
	p.unidad,
	p.nivel,
	p.especifico,
	cu.txt cargo,
	tp.txt tipo,
	pv.txt provision,
	ad.txt administracion,
	fr.txt formacion,
	g.val grupo,
	o.val observacion,
	c.val cuerpo,
	t.val titulacion
from 
	puesto p
	left join cargo cu on cu.id=p.cargo
	left join tipo_puesto tp on tp.id=p.tipo
	left join provision pv on pv.id=p.provision
	left join administracion ad on ad.id=p.administracion
	left join formacion fr on fr.id=p.formacion
	left join g on g.id=p.id
	left join o on o.id=p.id
	left join c on c.id=p.id
	left join t on t.id=p.id
	left join unidad ON unidad.id=p.unidad
;
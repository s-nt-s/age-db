SELECT
	p.id,
	coalesce(pg.grupo, 'NULL') grupo,
	p.nivel,
	p.cargo,
	p.unidad,
	u.centro,
	c.ministerio,
	p.localidad,
	l.provincia,
	pr.pais,
	p.tipo,
	p.provision,
	p.vacante,
	p.especifico + n.destino + coalesce(g.base, 0) + coalesce(g.extra_base, 0) sueldo
FROM
	puesto p
	join nivel n on p.nivel = n.id
	join localidad l on l.id=p.localidad
	join provincia pr on l.provincia=pr.id
	join unidad u on u.id=p.unidad
	join centro c on c.id=u.centro
	left join puesto_grupo pg ON p.id=pg.puesto
	left join grupo g ON g.id=pg.grupo
;
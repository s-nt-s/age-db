#!/bin/bash -li

cd "$(dirname "$0")"

schemaspy --out organismos.svg --size large -i 'UNIDAD|CENTRO|MINISTERIO|LOCALIDAD|PROVINCIA|PAIS' ../out/age.sqlite

schemaspy --out puestos.svg --size large -i '(PUESTO|UNIDAD|CARGO|LOCALIDAD|PROVISION|ADMINISTRACION|FORMACION|TITULACION|OBSERVACION|CUERPO).*' ../out/age.sqlite

schemaspy --out age.svg -rows --size large ../out/age.sqlite
#!/bin/bash -li

cd "$(dirname "$0")"

schemaspy --out organismos.svg --size large -i 'UNIDAD|CENTRO|MINISTERIO|LOCALIDAD|PROVINCIA|PAIS' ../db/age.sqlite

schemaspy --out puestos.svg --size large -i '(PUESTO|UNIDAD|CARGO|LOCALIDAD|PROVISION|ADMINISTRACION|FORMACION|TITULACION|OBSERVACION|CUERPO).*' ../db/age.sqlite

schemaspy --out age.svg -rows --size large ../db/age.sqlite
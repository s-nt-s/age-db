#!/bin/bash
set -e

cd "$(dirname "$0")"
mkdir -p aux/

echo ""
cp age.sqlite "aux/age.sqlite"
cp "config.load" "aux/config.load"
sed -e '/^\s*;*\s*$/d' -i "aux/config.load"
for t in $(sqlite3 "aux/age.sqlite" "SELECT name FROM sqlite_schema WHERE type='table';"); do
    for c in $(sqlite3 "aux/age.sqlite" "select name from pragma_table_info('$t') where \"notnull\"=1;"); do
        echo "  DO \$\$ ALTER TABLE $t ALTER COLUMN $c SET NOT NULL; \$\$ " >> "aux/config.load"
    done
    for c in $(sqlite3 "aux/age.sqlite" "select name from pragma_table_info('$t') where \"type\"='TEXT';"); do
        echo "  DO \$\$ ALTER TABLE $t ALTER COLUMN $c SET DATA TYPE TEXT COLLATE \"es-ES-x-icu\"; \$\$ " >> "aux/config.load"
    done
done
for t in $(sqlite3 "aux/age.sqlite" "SELECT name FROM sqlite_schema WHERE type='table';"); do
        echo "  DO \$\$ ALTER TABLE $t ENABLE ROW LEVEL SECURITY; \$\$ " >> "aux/config.load"
        echo "  DO \$\$ ALTER TABLE $t FORCE ROW LEVEL SECURITY; \$\$ " >> "aux/config.load"
        echo "  DO \$\$ CREATE POLICY read_policy ON $t FOR SELECT USING (true); \$\$ " >> "aux/config.load"
done
echo ";" >> "aux/config.load"
echo "public: build remote"
cat "aux/config.load"
pgloader "aux/config.load"

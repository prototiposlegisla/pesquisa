# -*- coding: utf-8 -*-
"""
Parser de arquivos ISO 2709 exportados do iAH/CDS-ISIS da Camara Municipal de SP.

Formato observado:
- Cada registro comeca com um leader de 24 chars (tamanho do registro etc.)
- Seguido de um directory (entradas de 12 chars: tag3 + len4 + pos5)
- Seguido dos dados separados por #
- Registro termina com ##
- Quebras de linha (\r\n) aparecem dentro dos dados

A chave: o # é o separador de campos no CDS-ISIS.
Os campos seguem a ordem do directory.

Tags da base legis:
  001 = Codigo interno (ex: L18407, AC1695, DLE81)
  005 = Tipo por extenso (ex: Lei, Ato da CMSP, Resolucao da CMSP)
  006 = Numero com ponto (ex: 18.407)
  010 = Data (ex: 19/01/2026)
  021 = Flag (sempre "1"?)
  025 = Ementa
  030 = Tipo de projeto origem (ex: Projeto de Lei)
  031 = Numero do projeto
  032 = Autor(es) do projeto (repetitivo)
  033 = Ano do projeto
  035 = Publicacao (DOC ...)
  042 = Revogacao
  045 = Notas
  050 = Legislacao explicativa (repetitivo, com ^t para refs)
  070 = Palavras-chave/indexacao (repetitivo, entre <>)
  080 = Iniciais catalogacao (ex: MFO, MBS)
  005 = (no final) Tipo em maiusculo (LEI, ATO DA CMSP, etc.)
"""
import sys
import json
import os
import re


def parse_iso2709_isis(filepath, encoding='utf-8'):
    """
    Parse arquivo ISO 2709 do CDS-ISIS.

    O servidor exporta o ISO 2709 como texto com line-wrapping (\r\n a cada ~80 cols).
    Estrategia: remover TODOS os \r\n primeiro, depois parsear o stream limpo.
    Os registros terminam com ## e cada um comeca com um leader de 5 digitos.
    """
    with open(filepath, 'rb') as f:
        raw = f.read()

    # Remover TODAS as quebras de linha (artefato do export texto)
    raw = raw.replace(b'\r\n', b'').replace(b'\r', b'').replace(b'\n', b'')

    records = []
    pos = 0

    while pos < len(raw):
        # Leader: 24 bytes
        if pos + 24 > len(raw):
            break

        leader = raw[pos:pos+24]

        try:
            record_length = int(leader[0:5])
            base_address = int(leader[12:17])
        except ValueError:
            pos += 1
            continue

        # Sem \r\n, o record_length e' exato
        if pos + record_length > len(raw):
            break

        record_bytes = raw[pos:pos+record_length]

        # Directory: bytes 24 ate base_address
        dir_bytes = record_bytes[24:base_address]

        # Parse directory: cada entrada = 12 bytes (tag3 + len4 + pos5)
        tags_order = []
        dir_str = dir_bytes.decode(encoding, errors='replace')
        i = 0
        while i + 12 <= len(dir_str):
            tag = dir_str[i:i+3]
            try:
                flen = int(dir_str[i+3:i+7])
                fpos = int(dir_str[i+7:i+12])
            except ValueError:
                break
            tags_order.append((tag, flen, fpos))
            i += 12

        if not tags_order:
            pos += record_length
            continue

        # Dados: a partir de base_address
        data_bytes = record_bytes[base_address:]

        # IMPORTANTE: O directory ISO 2709 usa offsets em BYTES, nao em caracteres.
        # Com UTF-8 multi-byte (e.g. nº, ç, ã), fatiar string desloca os campos.
        # Solucao: fatiar BYTES primeiro, depois decodificar cada campo.
        record = {}
        for tag, flen, fpos in tags_order:
            value = data_bytes[fpos:fpos+flen].decode(encoding, errors='replace')
            # Remover terminador de campo (#) no final
            value = value.rstrip('#').strip()

            if tag in record:
                if isinstance(record[tag], list):
                    record[tag].append(value)
                else:
                    record[tag] = [record[tag], value]
            else:
                record[tag] = value

        if record:
            records.append(record)

        pos += record_length

    return records


def transform_record(rec):
    """Transforma um registro parseado em formato limpo."""

    codigo = rec.get('001', '')
    tipo_extenso = rec.get('005', '')
    if isinstance(tipo_extenso, list):
        tipo_extenso = tipo_extenso[0]

    # Mapear tipo
    tipo_map = {
        'Lei': 'LEI',
        'Ato da CMSP': 'ATO',
        'Resolução da CMSP': 'RESOLUCAO',
        'Resolucao da CMSP': 'RESOLUCAO',
        'Decreto Legislativo': 'DECRETO LEGISLATIVO',
        'Emenda': 'EMENDA',
        'Emenda à Lei Orgânica': 'EMENDA',
    }
    tipo = tipo_map.get(tipo_extenso, tipo_extenso)

    numero = rec.get('006', '').replace('.', '')

    data = rec.get('010', '')

    ementa = rec.get('025', '')

    # Autores (032 pode ser repetitivo)
    autores_raw = rec.get('032', '')
    if isinstance(autores_raw, list):
        autores = ' | '.join(autores_raw)
    else:
        autores = autores_raw

    publicacao = rec.get('035', '')

    tipo_projeto = rec.get('030', '')
    num_projeto = rec.get('031', '')
    ano_projeto = rec.get('033', '')
    projeto = ''
    if tipo_projeto and num_projeto:
        projeto = f"{tipo_projeto} {num_projeto}"
        if ano_projeto:
            projeto += f"/{ano_projeto}"

    # Indexacao (070, repetitivo, entre <>)
    idx_raw = rec.get('070', [])
    if isinstance(idx_raw, str):
        idx_raw = [idx_raw]
    indexacao = []
    for item in idx_raw:
        clean = item.strip('<>').strip()
        if clean:
            indexacao.append(clean)

    notas = rec.get('045', '')

    revogacao = rec.get('042', '')

    leg_expl = rec.get('050', '')
    if isinstance(leg_expl, list):
        leg_expl = ' | '.join(leg_expl)

    return {
        'codigo': codigo,
        'tipo': tipo,
        'numero': numero,
        'data': data,
        'ementa': ementa,
        'autores': autores,
        'publicacao': publicacao,
        'projeto': projeto,
        'indexacao': ' | '.join(indexacao),
        'notas': notas,
        'revogacao': revogacao,
        'legislacao_explicativa': leg_expl,
    }


def main():
    sys.stdout.reconfigure(encoding='utf-8')

    if len(sys.argv) < 2:
        print("Uso: python parse_iso.py <arquivo.iso> [--json output.json] [--stats]")
        sys.exit(1)

    filepath = sys.argv[1]
    output_json = None
    show_stats = False

    for i, arg in enumerate(sys.argv):
        if arg == '--json' and i + 1 < len(sys.argv):
            output_json = sys.argv[i + 1]
        if arg == '--stats':
            show_stats = True

    print(f"Parseando: {filepath}")
    print(f"Tamanho: {os.path.getsize(filepath):,} bytes")

    records = parse_iso2709_isis(filepath)
    print(f"Registros parseados: {len(records)}")

    if not records:
        print("Nenhum registro encontrado!")
        sys.exit(1)

    transformed = [transform_record(r) for r in records]

    if show_stats or not output_json:
        tipos = {}
        for r in transformed:
            t = r['tipo']
            tipos[t] = tipos.get(t, 0) + 1

        print(f"\nDistribuicao por tipo:")
        for t, count in sorted(tipos.items(), key=lambda x: -x[1]):
            print(f"  {t}: {count}")

        print(f"\nPrimeiro registro:")
        for key, value in transformed[0].items():
            print(f"  {key}: {str(value)[:120]}")

        print(f"\nUltimo registro:")
        for key, value in transformed[-1].items():
            print(f"  {key}: {str(value)[:120]}")

        # Campos preenchidos
        print(f"\nCampos preenchidos:")
        for field in ['codigo', 'tipo', 'numero', 'data', 'ementa', 'autores', 'publicacao', 'projeto', 'indexacao', 'notas', 'revogacao']:
            filled = sum(1 for r in transformed if r.get(field))
            pct = 100 * filled / len(transformed)
            print(f"  {field}: {filled}/{len(transformed)} ({pct:.1f}%)")

        # Tags brutas
        all_tags = set()
        for r in records:
            all_tags.update(r.keys())
        print(f"\nTags ISIS encontradas: {sorted(all_tags)}")

    if output_json:
        with open(output_json, 'w', encoding='utf-8') as f:
            json.dump(transformed, f, ensure_ascii=False, indent=2)
        print(f"\nSalvo em: {output_json}")


if __name__ == '__main__':
    main()

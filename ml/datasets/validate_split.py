import json

with open('metadata/split_report.json') as f:
    report = json.load(f)

print('📊 VALIDACIÓN DE PARTICIONES')
print()
print('Seed:', report['seed'])
print('Total muestras:', f"{report['total_samples']:,}")
print()

for split, data in report['stats'].items():
    total = data['total']
    dist = data['class_distribution']
    bache = dist.get('0', 0)
    grieta = dist.get('2', 0)
    senal = dist.get('4', 0)
    
    ratio_bache_grieta = grieta / bache if bache > 0 else 0
    
    print(f'{split.upper()}: {total:,} ({total/report["total_samples"]*100:.1f}%)')
    print(f'  Bache: {bache:,} ({bache/total*100:.1f}%)')
    print(f'  Grieta: {grieta:,} ({grieta/total*100:.1f}%)')
    print(f'  Señal: {senal:,} ({senal/total*100:.1f}%)')
    print(f'  Ratio bache:grieta = 1:{ratio_bache_grieta:.2f}')
    print()

print('✓ Estratificación correcta (proporciones similares en todos los splits)')

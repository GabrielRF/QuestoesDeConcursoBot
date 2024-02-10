import os
import sys
import yaml

def lista_bancas():
    bancas = os.listdir('questoes')
    return bancas

def lista_concursos(banca):
    concursos = os.listdir(f'questoes/{banca}')
    return concursos

def lista_provas(banca, concurso):
    provas = os.listdir(f'questoes/{banca}/{concurso}')
    return provas

def testa_campo(questao, campo):
    try:
        questao[campo]
        return True
    except KeyError:
        return False

def testa_questao(questao, i):
    for campo in ['enunciado', 'alternativas']:
        teste = testa_campo(questao, campo)
        if not teste:
            print(f'\t\t\tCampo {campo} ausente na questao {i+1}')
            return 1
    return 0

if __name__ == "__main__":
    bancas = lista_bancas()
    resultado_final = 0
    for banca in bancas:
        print(f'{banca}')
        concursos = lista_concursos(banca)
        for concurso in concursos:
            print(f'\t{concurso}')
            provas = lista_provas(banca, concurso)
            for prova in provas:
                if '.yml' not in prova:
                    continue
                print(f'\t\t{prova}')
                with open(f'questoes/{banca}/{concurso}/{prova}') as arquivo:
                    arquivo_prova = yaml.safe_load(arquivo)
                    for i, questao in enumerate(arquivo_prova['questoes']):
                        resultado_final = resultado_final + testa_questao(questao, i)
    if resultado_final:
        sys.exit(f'Erros: {resultado_final}')

<img align="right" alt="Questões de Concurso Bot Logo" width="30%" height="auto" src="https://github.com/GabrielRF/QuestoesDeConcursoBot/blob/main/utils/icone.jpg?raw=true">

# Questões de Concurso Bot

📚 Estude no Telegram!

[![Deploy](https://github.com/GabrielRF/QuestoesDeConcursoBot/actions/workflows/deploy.yml/badge.svg)](https://github.com/GabrielRF/QuestoesDeConcursoBot/actions/workflows/deploy.yml)
[![Teste Questões](https://github.com/GabrielRF/QuestoesDeConcursoBot/actions/workflows/Teste_Questoes.yml/badge.svg)](https://github.com/GabrielRF/QuestoesDeConcursoBot/actions/workflows/Teste_Questoes.yml)

## Adicionar questões

> **Toda ajuda é bem vinda!**

A organização das questões segue o esquema abaixo:

```
    📂 questoes
        📂 <Banca 1>
            📂 <Ano e Nome do Concurso>
                📝 <Matéria 1.yml>
                📝 <Matéria 2.yml>
        📂 <Banca 2>
            📂 <Ano e Nome do concurso 1>
                📝 <Matéria 1.yml>
                📝 <Matéria 2.yml>
            📂 <Ano e Nome do concurso 2>
                📝 <Matéria 1.yml>
                🖼 <Imagem Questão 1.jpg>
                📝 <Matéria 2.yml>
```

Os arquivos das matérias, `Matéria.yml`, têm a seguinte estrutura:

```yml
---
materia: <Nome completo da matéria>
questoes:
  - cargo: <Cargo> # Questão 1
    enunciado: <Enunciado em uma linha só>
    alternativas:
      - '<Alternativa certa>'
      - '<Alternativa errada>'

...

  - cargo: <Cargo> # Questão n
    enunciado: |
      <Linha 1 do enunciado>
      ...
      <Linha n do enunciado>
    alternativas:
      - '<Alternativa certa>'
      - '<Alternativa errada 1>'
      - ...
      - '<Alternativa errada n>'
    explicacao: <Explicacao da resposta>
    imagem: <Imagem da questão>
```
Sendo:
* `cargo`: Cargo da prova da questão.
* `enunciado`: Enunciado da questão.
* `alternativas`: Alternativas de resposta, sendo a **primeira** da lista obrigatoriamente a **alternativa correta**.
* `explicacao`: Explicação da resposta em no máximo 200 caracteres. _Não havendo explicação, remova o campo da questão._
* `imagem`: Imagem da questão. Usar a url da imagem obrigatoriamente. _Não havendo imagem, remova o campo da questão._ [Clique aqui para mais informações sobre o envio de imagens.](#envio-de-imagens)

### Envio de imagens

O campo `imagem` em uma questão é totalmente opcional, não devendo ser usado caso a questão não exija uma imagem. O campo, caso necessário, deve ser preenchido com uma _URL_. Não sendo possível, envie a imagem para o repositório, colocando-a na mesma pasta do arquivo de questões. Nomeie a imagem com:
```
<Matéria> <Numero da questao na prova original>.<formato>
```
Use no campo imagem o valor
```
https://github.com/GabrielRF/QuestoesDeConcursoBot/blob/main/questoes/<BANCA>/<PROVA>/imagens/<ARQUIVO DA IMAGEM>?raw=true
```

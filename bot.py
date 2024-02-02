from utils import anuncieaqui
import os
import random
import redis
import sqlite3
import telebot
import time
import yaml

TOKEN = open('utils/token.conf', 'r').read().strip()
bot = telebot.TeleBot(TOKEN)
db = 'utils/usuarios.sqlite'
paginacao = 4

def verifica_e_adiciona_usuario(user_id):
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE user_id=?", (user_id,))
    existing_user = cursor.fetchone()

    if not existing_user:
        cursor.execute("INSERT INTO usuarios (user_id) VALUES (?)", (user_id,))
        conn.commit()

    conn.close()

def inicia_tempo(user_id):
    redis_set(f'{user_id}_tempo', time.time())

def calculo_tempo(user_id):
    tempo = time.time() - float(redis_get(f'{user_id}_tempo'))
    return time.strftime("%H:%M:%S", time.gmtime(tempo))

def initial_commands(user_id):
    bot.set_my_commands([
        telebot.types.BotCommand('start', 'Início do bot'),
        telebot.types.BotCommand('info', 'Informações'),
        telebot.types.BotCommand('pix', 'Faça uma doação')
    ], scope=telebot.types.BotCommandScopeChat(f'{user_id}'))

def remove_button(user_id):
    bot.edit_message_reply_markup(
        user_id,
        redis_get(f'{user_id}#botao_id')
    )

def new_button_and_edit(user_id, message_id, button):
    return bot.edit_message_reply_markup(
        user_id,
        message_id,
        reply_markup=button
    )

def remove_button_and_edit(query):
    clicked_data = query.data
    for data in query.json['message']['reply_markup']['inline_keyboard']:
        if data[0]['callback_data'] == clicked_data:
            clicked = data[0]['text']
    bot.edit_message_text(
        text=f'{query.message.text}\n<b>{clicked}</b>',
        chat_id=query.from_user.id,
        message_id=redis_get(f'{query.from_user.id}#botao_id'),
        parse_mode='HTML'
    )

def redis_clean(chatid): # Redis - Limpar valor
    r = redis.Redis(host='localhost', port=6379, db=0)
    r.delete(chatid)

def redis_get(chatid): # Redis - Ler valor
    r = redis.Redis(host='localhost', port=6379, db=0)
    return r.get(chatid).decode('utf-8')

def redis_set(chatid, val): # Redis - Escrever valor
    r = redis.Redis(host='localhost', port=6379, db=0)
    r.set(chatid, val)

def poll_options(questoes):
    opcoes = []
    for opcao in questoes['alternativas']: opcoes.append(str(opcao))
    random.shuffle(opcoes)
    correta = opcoes.index(str(questoes['alternativas'][0]))
    return opcoes, correta

def get_value(array, value):
    try:
        return f"{array[value]}"
    except KeyError:
        return None

def materias_query(query):
    remove_button_and_edit(query)
    banca, concurso, materia = query.data.split('#')
    redis_set(query.from_user.id, f'{banca}#{concurso}#{materia}')
    inicia_tempo(query.from_user.id)
    send_poll(query.from_user.id, query.data)

def get_materia_name(caminho):
    with open(f'questoes/{caminho}', 'r') as arquivo:
        arquivo_questoes = yaml.safe_load(arquivo)
    try:
        materia_nome_completo=arquivo_questoes['materia']
    except KeyError:
        materia_nome_completo=caminho.split('#')[-1]
    return materia_nome_completo

def concurso_query(query, page=0):
    try:
        banca, concurso = query.data.split('#')
        redis_set(query.from_user.id, f'{banca}#{concurso}')
        remove_button_and_edit(query)
        editar=False
    except ValueError:
        banca, concurso = redis_get(query.from_user.id).split('#')
        editar=True
        #bot.delete_message(query.from_user.id, query.message.id)
    button = telebot.types.InlineKeyboardMarkup()
    materias = os.listdir(f'questoes/{banca}/{concurso}')
    materias = sorted(materias)
    start = page*paginacao
    end = (page+1)*paginacao
    for materia in sorted(materias)[start:end]:
        with open(f'questoes/{banca}/{concurso}/{materia}', 'r') as arquivo:
            arquivo_questoes = yaml.safe_load(arquivo)
        materia_nome_completo = get_materia_name(f'{banca}/{concurso}/{materia}')
        if '.yml' not in materia:
            continue
        button.row(
            telebot.types.InlineKeyboardButton(
                materia_nome_completo.replace('.yml', '')[:30],
                callback_data=f'{banca}#{concurso}#{materia}'
            )
        )
    botao_voltar = telebot.types.InlineKeyboardButton(
        '« Anterior',
        callback_data=f'page_materia {page-1}'
    )
    botao_avancar = telebot.types.InlineKeyboardButton(
        'Próxima »',
        callback_data=f'page_materia {page+1}'
    )
    if len(materias) > paginacao:
        if start == 0:
            button.row(botao_avancar)
        elif end >= len(materias):
            button.row(botao_voltar)
        else:
            button.row(botao_voltar, botao_avancar)
    message_text = 'Escolha uma matéria:'
    if editar:
        materia_msg = new_button_and_edit(
            query.from_user.id,
            query.message.id,
            button
        )
    else:
        materia_msg = bot.send_message(
            query.from_user.id,
            message_text,
            reply_markup=button
        )
    redis_set(f'{query.from_user.id}#botao_id', materia_msg.id)

def bancas_query(query):
    remove_button_and_edit(query)
    banca = f'{query.data.replace("Banca ", "")}'
    concursos = os.listdir(f'questoes/{banca}')
    button = telebot.types.InlineKeyboardMarkup()
    for concurso in reversed(sorted(concursos)):
        button.row(
            telebot.types.InlineKeyboardButton(
                concurso,
                callback_data=f'{banca}#{concurso}'
            )
        )
    concurso_msg = bot.send_message(
        query.from_user.id,
        'Escolha o concurso:',
        reply_markup=button
    )
    redis_set(f'{query.from_user.id}#botao_id', concurso_msg.id)

@bot.callback_query_handler(lambda q: q.data == 'Pular')
def skip_question(call):
    try:
        bot.answer_callback_query(call.id)
    except:
        pass
    try:
        bot.delete_message(call.from_user.id, call.message.id)
    except:
        pass
    send_poll(call.from_user.id)

@bot.callback_query_handler(func=lambda q:True)
def banca_query(query):
    try:
        bot.answer_callback_query(query.id)
    except:
        pass
    if 'Banca ' in query.data:
        bancas_query(query)
    elif 'page_materia ' in query.data:
        page = query.data.split(' ')[1]
        concurso_query(query,int(page))
    elif len(query.data.split('#')) == 2:
        concurso_query(query)
    else:
        materias_query(query)

@bot.message_handler(commands=['pix'])
def send_rules(message):
    if message.chat.id < 0:
        return
    else:
        bot.send_photo(message.chat.id,
            'AgACAgEAAxkBAAIODmW7suEuE8g5IEts5iuXVaHBJeqJAAKjrTEbfhvgRZLf' +
            '-IIi8YBqAQADAgADcwADNAQ',
            caption='Envie um pix para a chave <code>bots@grf.xyz</code>',
            parse_mode='HTML'
        )

@bot.message_handler(commands=["info"])
def informacoes(message):
    redis_clean(message.from_user.id)
    info_message = (
        '📚 <b>@QuestoesDeConcursoBot</b>\n\n'
        '🔧 Código fonte e envio questões:\n' +
        'https://github.com/GabrielRF/QuestoesDeConcursoBot\n\n' +
        '🤖 Autor: @GabrielRF'
    )
    bot.send_message(
        message.from_user.id,
        info_message,
        parse_mode='HTML',
        disable_web_page_preview=True
    )

@bot.message_handler(commands=["parar", "Parar"])
def parar_questoes(message):
    try:
        bot.delete_message(message.from_user.id, message.id)
        bot.delete_message(message.from_user.id, message.id-1)
    except:
        pass
    try:
        send_results(message.from_user.id)
    except:
        pass
    #definir_banca(message)

@bot.message_handler(commands=["start", "bancas", "Bancas"])
def definir_banca(message):
    verifica_e_adiciona_usuario(message.from_user.id)
    initial_commands(message.from_user.id)
    bancas = os.listdir('questoes')
    button = telebot.types.InlineKeyboardMarkup()
    redis_clean(message.from_user.id)
    redis_set(f'{message.from_user.id}_acertos', 0)
    redis_set(f'{message.from_user.id}_erros', 0)
    for banca in sorted(bancas):
        button.row(
            telebot.types.InlineKeyboardButton(
                banca,
                callback_data=f'Banca {banca}'
            )
        )
    start_message = (
        f'📚 <b>@QuestoesDeConcursoBot</b>\n\n' +
        f'<b>Olá, {message.from_user.first_name}</b>,\n' +
        f'A qualquer momento use o <code>Menu</code> para ver as opções do bot\n'
        f'Para iniciar uma atividade, selecione uma banca abaixo:' 
    )
    msg = bot.send_message(
        message.from_user.id,
        start_message,
        reply_markup=button,
        parse_mode='HTML'
    )
    redis_set(f'{message.from_user.id}#botao_id', msg.id)

def send_results(user_id):
    try:
        banca, concurso, materia, i = redis_get(user_id).split('#')
        i = int(i)
    except ValueError:
        banca, concurso, materia = redis_get(user_id).split('#')
        i = 0
    acertos = redis_get(f'{user_id}_acertos')
    erros = redis_get(f'{user_id}_erros')

    initial_commands(user_id)

    materia_nome_completo = get_materia_name(f'{banca}/{concurso}/{materia}')

    end_message = (
        f'📚 <b>@QuestoesDeConcursoBot</b>\n\n'
        f'<b>{banca} - {concurso} - {materia_nome_completo}</b>\n' +
        f'<i>Fim da atividade</i>.\n\n' +
        f'⏰ Duração: {calculo_tempo(user_id)}\n' +
        f'✅ Acertos: {acertos}\n' +
        f'❌ Erros: {erros}\n\n' +
        f'⬇️ Clique em <code>Menu</code> e escolha uma das opções.'
    )

    try:
        anuncieaqui.send_message(
            TOKEN,
            user_id,
            end_message
        )
    except:
        bot.send_message(
            user_id,
            end_message,
            parse_mode='HTML'
        )

def send_poll(user_id, query_data=None):
    bot.send_chat_action(user_id, 'typing')
    try:
        banca, concurso, materia, i = query_data.split('#')
    except ValueError:
        banca, concurso, materia = query_data.split('#')
        i = 0
    except AttributeError:
        banca, concurso, materia, i = redis_get(user_id).split('#')
    i = int(i)
    with open(f'questoes/{banca}/{concurso}/{materia}', 'r') as arquivo:
        arquivo_questoes = yaml.safe_load(arquivo)
    try:
        questoes = arquivo_questoes['questoes'][i]
    except IndexError:
        send_results(user_id)
        return

    materia_nome_completo = get_materia_name(f'{banca}/{concurso}/{materia}')
    explicacao=get_value(arquivo_questoes['questoes'][i], 'explicacao')
    if explicacao: explicacao=explicacao[:200]
    imagem=get_value(arquivo_questoes['questoes'][i], 'imagem')
    cargo=get_value(arquivo_questoes['questoes'][i], 'cargo')
    tamanho = len(arquivo_questoes['questoes'])

    enunciado = (
        f"*[{i+1}/{tamanho}] {banca} - "
        f"{concurso} - {materia_nome_completo} *\n"
        f"{cargo}\n\n"
        f"{questoes['enunciado']}"
    )
    if imagem:
        enunciado = f'[ ]({imagem}){enunciado}'
    opcoes, correta = poll_options(questoes)

    try:
        msg = bot.send_message(
            user_id,
            enunciado,
            parse_mode='Markdown'
        )
    except Exception as e:
        if 'message is too long' in str(e):
            enunciado_split = enunciado.split('\n')
            msg_id = None
            break_every = 5
            for palavra in range(0, len(enunciado_split)-1, break_every):
                s = '\n'
                msg = bot.send_message(
                    user_id,
                    s.join(enunciado_split[palavra:palavra+break_every]),
                    parse_mode='Markdown',
                    reply_to_message_id=msg_id
                )
                msg_id = msg.id
                bot.send_chat_action(user_id, 'typing')

    button = telebot.types.InlineKeyboardMarkup()
    button.row(
        telebot.types.InlineKeyboardButton(
            'Pular',
            callback_data=f'Pular'
        )
    )
    redis_set(user_id, f'{banca}#{concurso}#{materia}#{i+1}')

    try:
        poll_msg = bot.send_poll(
            user_id,
            f'Resposta [{i+1}/{tamanho}]:',
            opcoes,
            reply_to_message_id=msg.id,
            type="quiz",
            #open_period=600,
            is_anonymous=False,
            allows_multiple_answers=False,
            correct_option_id=correta,
            explanation=explicacao,
            reply_markup=button
        )
    except Exception as e:
        alternativas = ''
        novas_opcoes = []
        letras = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K']
        if 'poll options length must not exceed 100' in str(e):
            for y, alternativa in enumerate(opcoes, start=0):
                alternativas = f'{alternativas}\n\n`{letras[y]}`: {alternativa}'
                novas_opcoes.append(f'Alternativa {letras[y]}')
            msg = bot.reply_to(
                msg,
                alternativas,
                parse_mode='Markdown'
            )
            poll_msg = bot.send_poll(
                user_id,
                f'Resposta [{i+1}/{tamanho}]:',
                novas_opcoes,
                reply_to_message_id=msg.id,
                type="quiz",
                #open_period=600,
                is_anonymous=False,
                allows_multiple_answers=False,
                correct_option_id=correta,
                explanation=explicacao,
                reply_markup=button
            )

    redis_set(user_id, f'{banca}#{concurso}#{materia}#{i+1}')
    redis_set(f'{user_id}#botao_id', poll_msg.id)
    redis_set(f'{user_id}_answer', correta)
    bot.set_my_commands([
        telebot.types.BotCommand('parar', 'Parar atividade')
    ], scope=telebot.types.BotCommandScopeChat(f'{user_id}'))

@bot.poll_answer_handler(func=lambda m: True)
def poll_update(poll):
    resposta = poll.option_ids[0]
    user_id = poll.user.id

    acertos = redis_get(f'{user_id}_acertos')
    erros = redis_get(f'{user_id}_erros')
    if redis_get(f'{user_id}_answer') == str(resposta):
        acertos = int(acertos)+1
    else:
        erros = int(erros)+1
    redis_set(f'{user_id}_acertos', acertos)
    redis_set(f'{user_id}_erros', erros)

    remove_button(user_id)

    send_poll(poll.user.id, redis_get(poll.user.id))

if __name__ == "__main__":
    bot.infinity_polling(
        allowed_updates=[
            'message',
            'poll',
            'callback_query',
            'poll_answer'
        ]
    )

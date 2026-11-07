# 4. User Stories — BATTLE CARD-GAME

Formato: **"Como [ator], quero [ação] para que [valor de negócio]"**, com critérios de aceite em **Gherkin** (Dado / Quando / Então).
Cada história referencia os requisitos (`RFxx`) e os casos de uso (`UCxx`). Prioridade: **Alta / Média / Baixa**.

Convenção dos cenários: o prefixo `Cenário` descreve o comportamento; `Esquema do Cenário` usa uma tabela de exemplos.

---

## Épico 1 — Conta e acesso

### US01 — Criar conta
**Como** visitante, **quero** criar uma conta com nome, senha e e-mail **para que** eu possa jogar com um perfil só meu. — *RF01, RF02, RF07 · UC01 · Alta*

```gherkin
# language: pt
Funcionalidade: Cadastro de conta

  Cenário: Cadastro válido cria conta, deck inicial e Grimorium vazio
    Dado que não existe conta com o nome "Jogador1" nem com o e-mail "j1@example.com"
    Quando eu envio nome "Jogador1", senha "senha123", repetição "senha123" e e-mail "j1@example.com"
    Então a conta é criada com perfil "GREEN" e status 1
    E a senha é gravada como hash e nunca em texto puro
    E o "Deck 1" contém exatamente 40 cartas, com no máximo 3 cópias de cada Card_ID
    E nenhuma carta do deck é Foil ou Shiny
    E o Grimorium da conta existe com 0 cartas

  Esquema do Cenário: Dados inválidos são recusados com mensagem por campo
    Quando eu envio nome "<nome>", senha "<senha>", repetição "<repete>" e e-mail "<email>"
    Então o cadastro é recusado com a mensagem "<mensagem>"
    E nenhuma conta é criada

    Exemplos:
      | nome            | senha     | repete    | email          | mensagem                                    |
      | Joa             | senha123  | senha123  | a@b.com        | O nome deve ter de 4 a 16 caracteres.       |
      | João1           | senha123  | senha123  | a@b.com        | Use apenas letras (sem acentos) e números.  |
      | Jogador1        | 12345     | 12345     | a@b.com        | A senha deve ter de 6 a 32 caracteres.      |
      | Jogador1        | senha123  | outra123  | a@b.com        | As senhas não conferem.                     |
      | Jogador1        | senha123  | senha123  | a@b           | Formato de e-mail inválido.                 |
```

### US02 — Garantir nome e e-mail únicos
**Como** visitante, **quero** saber enquanto digito se o nome e o e-mail estão disponíveis **para que** eu não perca tempo com um cadastro que será recusado. — *RF02 · UC01 · Média*

```gherkin
Funcionalidade: Disponibilidade de nome e e-mail

  Cenário: Nome já usado, sem diferenciar maiúsculas
    Dado que existe a conta "Jogador1"
    Quando eu digito o nome "jogador1" no cadastro
    Então vejo "Nome já em uso."

  Cenário: Corrida entre dois cadastros
    Dado que duas pessoas enviam o mesmo nome ao mesmo tempo
    Quando o servidor grava o primeiro cadastro
    Então o segundo é recusado com "nome ou e-mail já cadastrado"
    E apenas uma conta existe com aquele nome
```

### US03 — Entrar e sair do sistema
**Como** jogador, **quero** fazer login e logout **para que** apenas eu acesse a minha conta. — *RF03, RF05 · UC02 · Alta*

```gherkin
Funcionalidade: Login e logout

  Cenário: Login válido
    Dado que existe a conta "Jogador1" com senha "senha123"
    Quando eu envio nome "jogador1" e senha "senha123"
    Então a sessão é criada e eu vou para a seleção de servidor

  Cenário: Credenciais inválidas não revelam qual campo errou
    Quando eu envio nome "Jogador1" e senha "errada1"
    Então vejo "Nome ou senha inválidos."

  Cenário: Conta bloqueada não entra
    Dado que a conta "Jogador1" tem perfil "RED"
    Quando eu tento fazer login com a senha correta
    Então vejo "Nome ou senha inválidos."

  Cenário: Excesso de tentativas
    Dado que errei a senha 10 vezes em 5 minutos
    Quando tento novamente
    Então vejo "Muitas tentativas. Aguarde um pouco."

  Cenário: Páginas do jogo exigem sessão
    Dado que não estou logado
    Quando abro "/lobby/"
    Então sou redirecionado para "/login/"

  Cenário: Logout
    Dado que estou logado
    Quando clico em "Sair"
    Então a sessão é encerrada e volto à página inicial
```

### US04 — Sessão única por conta
**Como** jogador, **quero** que um novo login derrube a sessão anterior **para que** ninguém use minha conta em dois lugares ao mesmo tempo. — *RF04 · UC02 · Média*

```gherkin
Funcionalidade: Sessão única

  Cenário: Login em outro navegador encerra o primeiro
    Dado que estou logado no navegador 1 com conexões WebSocket abertas
    Quando faço login com a mesma conta no navegador 2
    Então as requisições do navegador 1 passam a responder "login necessário"
    E as conexões WebSocket do navegador 1 são fechadas com o código 4000
```

### US05 — Ver o status do jogo na página inicial
**Como** visitante, **quero** ver se o servidor está online e quantos jogadores estão conectados **para que** eu decida entrar agora. — *RF08 · Média*

```gherkin
Funcionalidade: Página inicial

  Cenário: Exibir status
    Dado que há 3 usuários conectados
    Quando abro a página inicial
    Então vejo "Servidor: Online" e "Usuários online: 3"
    E vejo os botões "Login" e "Criar conta"
```

---

## Épico 2 — Servidores, lobby e salas

### US06 — Escolher servidor
**Como** jogador, **quero** escolher o servidor em que vou jogar **para que** eu entre no lobby correto. — *RF09 · Média*

```gherkin
Funcionalidade: Seleção de servidor

  Cenário: Listar servidores ativos
    Dado que existem os servidores "Servidor 1" (ativo) e "Servidor 2" (inativo)
    Quando abro a seleção de servidor
    Então vejo apenas "Servidor 1" com seu número de usuários online

  Cenário: Entrar no lobby
    Quando clico em "Entrar" no "Servidor 1"
    Então abro o lobby daquele servidor
```

### US07 — Ver quem está online
**Como** jogador, **quero** ver a lista de contas logadas no lobby **para que** eu saiba com quem posso jogar ou conversar. — *RF10 · Média*

```gherkin
Funcionalidade: Lista de contas online

  Cenário: Atualização em tempo real
    Dado que estou no lobby
    Quando outra conta entra no mesmo servidor
    Então o nome dela aparece na minha lista sem recarregar a página
    Quando essa conta fecha todas as suas abas
    Então o nome dela some da lista
```

### US08 — Conversar no lobby
**Como** jogador, **quero** enviar mensagens a todos no lobby **para que** eu combine partidas. — *RF11 · UC04 · Média*

```gherkin
Funcionalidade: Chat do lobby

  Cenário: Mensagem entregue com hora e remetente
    Dado que estou no lobby
    Quando envio "Alguém para jogar?"
    Então todos no lobby veem "[hh:mm:ss] Jogador1: Alguém para jogar?"

  Cenário: Mensagem acima do limite
    Quando envio um texto com 127 caracteres
    Então vejo "Mensagem acima de 126 caracteres."
    E nada é enviado

  Cenário: Texto é exibido como texto, nunca como HTML
    Quando envio "<script>alert(1)</script>"
    Então os demais veem exatamente esse texto e nenhum script é executado

  Cenário: Limite de taxa
    Quando envio 6 mensagens em 5 segundos
    Então a sexta é recusada com "Muitas tentativas. Aguarde um pouco."
```

### US09 — Conversar em privado
**Como** jogador, **quero** enviar mensagem privada a um usuário online **para que** eu combine algo sem expor ao lobby. — *RF12 · UC04 · Baixa*

```gherkin
Funcionalidade: Chat privado

  Cenário: Mensagem privada entregue só aos dois
    Dado que "Jogador2" está online
    Quando envio a ele "Vamos jogar?" em privado
    Então somente "Jogador1" e "Jogador2" recebem a mensagem

  Cenário: Destinatário offline
    Dado que "Jogador3" está offline
    Quando tento enviar mensagem privada a ele
    Então vejo "Usuário não está online."
```

### US10 — Criar sala
**Como** jogador, **quero** criar uma sala escolhendo nome, modo e senha opcional **para que** eu jogue contra alguém ou teste sozinho. — *RF13, RF16 · UC05 · Alta*

```gherkin
Funcionalidade: Criação de sala

  Cenário: Sala 1x1 com senha
    Dado que estou no lobby e fora de qualquer sala
    Quando crio a sala "Duelo" no modo "1x1" com senha "abc"
    Então entro na sala como Jogador A
    E a sala aparece na lista como "ABERTA" com cadeado

  Cenário: Sala Debug não aceita segundo jogador
    Quando crio uma sala no modo "Debug"
    Então ela aparece na lista como não clicável

  Cenário: Estar em duas salas não é permitido
    Dado que já estou em uma sala
    Quando tento criar outra
    Então vejo "Você já está em uma sala."

  Cenário: Nome inválido
    Quando crio uma sala com nome vazio ou com mais de 24 caracteres
    Então vejo "Nome de sala inválido (1 a 24 caracteres)."
```

### US11 — Entrar em sala
**Como** jogador, **quero** entrar em uma sala aberta, inclusive buscando pelo ID **para que** eu jogue contra o dono dela. — *RF14 · UC05 · Alta*

```gherkin
Funcionalidade: Entrada em sala

  Cenário: Entrar em sala aberta
    Dado que existe a sala 7 "ABERTA" sem senha
    Quando clico em "Entrar" na sala 7
    Então entro como Jogador B
    E a sala passa a "READY"

  Cenário: Senha incorreta
    Dado que a sala 8 tem senha
    Quando informo a senha errada
    Então vejo "Senha da sala incorreta." e não entro

  Cenário: Sala cheia ou em batalha
    Dado que a sala 9 está "EM BATALHA"
    Quando tento entrar
    Então vejo "Não é possível entrar nesta sala."

  Cenário: Busca por ID inexistente
    Quando busco a sala 999
    Então vejo "Sala não encontrada."
```

### US12 — Convidar um jogador
**Como** jogador em uma sala aberta, **quero** convidar um usuário online **para que** ele entre rapidamente na minha sala. — *RF15, RF19 · UC05 · Baixa*

```gherkin
Funcionalidade: Convites

  Cenário: Convite recebido
    Dado que estou em uma sala "ABERTA"
    Quando convido "Jogador2", que está online
    Então "Jogador2" vê "Jogador1 convidou você para a sala N." com o botão "Entrar"
    E eu vejo "Convite enviado."

  Cenário: Convite sem sala
    Dado que não estou em nenhuma sala
    Quando tento convidar alguém
    Então vejo "Você precisa estar em uma sala aberta para convidar."
```

### US13 — Sair da sala sem deixá-la vazia
**Como** jogador, **quero** sair da sala **para que** eu volte ao lobby sem prejudicar quem ficou. — *RF16, RF18 · UC05 · Média*

```gherkin
Funcionalidade: Saída de sala

  Cenário: Jogador A sai e B assume
    Dado que A e B estão na sala
    Quando A sai da sala
    Então B passa a ser o Jogador A
    E a sala volta a "ABERTA" com os READY zerados

  Cenário: Última pessoa sai
    Dado que apenas A está na sala
    Quando A sai
    Então a sala é removida da lista

  Cenário: Sair durante a batalha
    Dado que há uma partida 1x1 em andamento
    Quando eu saio da sala
    Então perco por abandono sem Battlepoints e o adversário recebe 10 BP
```

### US14 — Conversar na sala
**Como** jogador, **quero** um chat da sala **para que** eu converse com meu adversário durante a partida. — *RF17 · UC04 · Baixa*

```gherkin
Funcionalidade: Chat da sala

  Cenário: Mensagem visível apenas aos ocupantes
    Dado que estou na sala 7
    Quando envio "Boa sorte!"
    Então os ocupantes da sala 7 veem a mensagem
    E ninguém no lobby a recebe
```

---

## Épico 3 — Decks e Grimorium

### US15 — Gerenciar meus decks
**Como** jogador, **quero** mover cartas entre meus decks e o Grimorium **para que** eu monte o deck que quero jogar. — *RF20, RF22 · UC03 · Alta*

```gherkin
Funcionalidade: Edição de decks

  Cenário: Mover carta do deck para o Grimorium
    Dado que o "Deck 1" tem 40 cartas
    Quando movo uma carta para o Grimorium
    Então o "Deck 1" mostra 39/40 e o Grimorium mostra 1/500

  Cenário: Limite de 40 cartas
    Dado que o "Deck 1" tem 40 cartas
    Quando tento mover para ele uma carta do Grimorium
    Então vejo "O deck já tem 40 cartas." e nada muda

  Cenário: Limite de 3 cópias por deck
    Dado que o "Deck 1" tem 3 cópias do Card_ID 12 e 39 cartas no total
    Quando tento mover a quarta cópia do Card_ID 12 para esse deck
    Então vejo "Máximo de 3 cartas iguais por deck."

  Cenário: Cópias iguais em decks diferentes
    Dado que o "Deck 1" tem 3 cópias do Card_ID 12
    Quando movo cópias do Card_ID 12 para o "Deck 2"
    Então até 3 cópias são aceitas no "Deck 2" também

  Cenário: Limite do Grimorium
    Dado que o Grimorium tem 500 cartas
    Quando tento mover mais uma para ele
    Então vejo "O Grimorium está cheio (500)."

  Cenário: Carta de outra conta
    Quando tento mover uma carta que pertence a outra conta
    Então vejo "Carta não encontrada."
```

### US16 — Criar, renomear e remover decks
**Como** jogador, **quero** criar, renomear e remover decks **para que** eu organize minhas estratégias. — *RF21 · UC03 · Média*

```gherkin
Funcionalidade: Ciclo de vida do deck

  Cenário: Criar deck em slot livre
    Dado que o slot 2 está vazio e liberado
    Quando clico em "Criar deck" no slot 2
    Então o deck é criado vazio, com o nome "Deck 2"

  Cenário: Renomear
    Quando renomeio o deck para "Fogo Rápido"
    Então o nome é exibido na aba do slot

  Cenário: Remover apenas deck vazio
    Dado que um deck tem cartas
    Quando tento removê-lo
    Então vejo "Só é possível remover decks vazios."

  Cenário: Slots premium
    Dado que minha conta não tem premium
    Então os slots 4, 5 e 6 aparecem bloqueados e não podem ser criados
```

### US17 — Escolher o deck das partidas
**Como** jogador, **quero** definir qual deck uso nas partidas **para que** o jogo use a minha escolha. — *RF23 · UC03 · Alta*

```gherkin
Funcionalidade: Seleção de deck

  Cenário: Selecionar deck
    Dado que o "Deck 2" existe
    Quando clico em "Usar este deck" no "Deck 2"
    Então o "Deck 2" aparece com uma estrela e passa a ser usado nas partidas

  Cenário: Deck inexistente ou bloqueado
    Quando tento selecionar um slot sem deck ou premium bloqueado
    Então vejo "Deck não encontrado."
```

---

## Épico 4 — Partida

### US18 — Começar a partida com READY
**Como** jogador, **quero** marcar READY com meu deck selecionado **para que** a partida comece quando os dois estiverem prontos. — *RF24 · UC06 · Alta*

```gherkin
Funcionalidade: READY

  Cenário: Início da partida 1x1
    Dado que A e B estão na sala, conectados e com decks de 40 cartas
    Quando ambos clicam em READY
    Então a sala passa a "EM BATALHA" e abre a escolha de X ou O

  Cenário: Deck incompleto
    Dado que meu deck selecionado tem 38 cartas
    Quando clico em READY
    Então vejo "O deck precisa ter exatamente 40 cartas (tem 38)." e não fico READY

  Cenário: Cancelar READY
    Dado que cliquei em READY e o adversário ainda não
    Quando clico em "Cancelar READY"
    Então volto ao estado não pronto
```

### US19 — Escolher X ou O e definir quem começa
**Como** jogador, **quero** escolher X ou O **para que** a iniciativa seja decidida de forma justa pelo servidor. — *RF25, RF26 · UC06 · Alta*

```gherkin
Funcionalidade: Escolha X/O e iniciativa

  Cenário: Cada jogador escolhe uma vez
    Dado que a janela de 10 segundos está aberta
    Quando escolho "X"
    Então o botão "X" e o "O" ficam desabilitados para mim
    E o adversário só pode escolher "O"

  Cenário: Quem não escolhe recebe o símbolo restante
    Dado que só eu escolhi "X" e os 10 segundos terminaram
    Então o adversário recebe "O"

  Cenário: Ninguém escolhe
    Dado que os 10 segundos terminaram sem escolhas
    Então os símbolos são sorteados

  Cenário: Servidor sorteia a iniciativa
    Quando os símbolos estão definidos
    Então o servidor sorteia "X" ou "O" e o jogador com aquele símbolo começa o turno 1

  Cenário: Escolher duas vezes ou escolher o símbolo do adversário
    Quando tento escolher de novo ou escolher o símbolo já escolhido pelo adversário
    Então a escolha é recusada
```

### US20 — Estado inicial da partida
**Como** jogador, **quero** começar com LIFE, MANA, mão e Avatar corretos **para que** a partida siga as regras do jogo. — *RF27 · UC06 · Alta*

```gherkin
Funcionalidade: Estado inicial

  Cenário: Configuração de cada jogador
    Quando a partida inicia
    Então cada jogador tem LIFE 20, MANA 1 e 5 cartas na mão
    E o deck de batalha está embaralhado, com as 35 cartas restantes
    E o descarte está vazio e visível
    E o Avatar de A está em (2,0) e o de B em (2,4)

  Cenário: Informação oculta
    Quando a partida inicia
    Então eu não vejo a mão nem o deck do adversário, apenas a quantidade de cartas
```

### US21 — Jogar o turno dentro do tempo
**Como** jogador, **quero** um turno de 45 segundos com contador visível **para que** a partida tenha ritmo e eu saiba quanto tempo resta. — *RF28, RF29, RF41, RF43 · UC07 · Alta*

```gherkin
Funcionalidade: Temporizador e fases do turno

  Cenário: Compra até 5 cartas
    Dado que tenho 3 cartas na mão e o deck tem cartas
    Quando começa o meu turno
    Então compro 2 cartas e fico com 5

  Cenário: DECK BURN
    Dado que tenho 3 cartas na mão e o deck está vazio
    Quando começa o meu turno
    Então perco 2 de LIFE

  Cenário: Contador de aviso
    Quando restam 15 segundos
    Então o contador muda para o estado de alerta

  Cenário: Tempo esgotado
    Quando os 45 segundos terminam
    Então o servidor encerra o turno e passa a vez ao adversário

  Cenário: Encerrar turno manualmente
    Quando clico em "Encerrar turno"
    Então a vez passa ao adversário imediatamente

  Cenário: Fim automático
    Dado que esgotei todas as ações possíveis
    Então o turno termina sozinho

  Cenário: Ação fora do turno
    Dado que é o turno do adversário
    Quando tento invocar uma carta
    Então vejo "Não é o seu turno."
```

### US22 — Mover o Avatar e meditar
**Como** jogador, **quero** andar com o Avatar ou, se ficar parado, meditar **para que** eu escolha entre posição e MANA. — *RF30, RF31 · UC07 · Alta*

```gherkin
Funcionalidade: Avatar e meditação

  Cenário: Andar um bloco
    Dado que meu Avatar está em (2,0)
    Quando ando para (2,1)
    Então o Avatar passa a (2,1) e não posso andar de novo neste turno

  Cenário: Movimento diagonal ou distante
    Quando tento andar para (3,1) ou (2,2)
    Então vejo "Bloco inválido."

  Cenário: Bloco ocupado por carta do adversário
    Quando tento andar para um bloco com carta do adversário
    Então vejo "Bloco ocupado por carta do adversário."

  Cenário: Pisar em carta própria
    Quando ando para um bloco com carta minha
    Então a carta é destruída e vai para o meu descarte

  Cenário: Meditação
    Dado que não andei com o Avatar e tenho MANA 2
    Quando o turno termina
    Então meu MANA passa a 3

  Cenário: Meditação respeita o limite
    Dado que tenho MANA 6 e não andei
    Quando o turno termina
    Então meu MANA continua 6
```

### US23 — Invocar cartas
**Como** jogador, **quero** invocar cartas ao redor do meu Avatar, viradas para cima ou para baixo **para que** eu monte minha força na arena. — *RF32, RF33, RF36 · UC07 · Alta*

```gherkin
Funcionalidade: Invocação

  Cenário: Invocar em bloco livre adjacente ou diagonal
    Dado que tenho uma carta SUMMON na mão e meu Avatar está em (2,0)
    Quando invoco em (3,1) com "Face-up"
    Então a carta aparece em (3,1) revelada
    E o MANA COST da carta é cobrado

  Cenário: Invocação face-down não cobra MANA
    Quando invoco virada para baixo
    Então o adversário vê apenas o verso e nenhum MANA é cobrado

  Cenário: Apenas uma invocação por turno
    Dado que já invoquei neste turno
    Quando tento invocar outra carta
    Então vejo "Só uma invocação por turno."

  Cenário: DOUBLE CAST
    Dado que invoquei uma carta e tenho MANA 1 ou mais
    Quando uso "DOUBLE CAST"
    Então pago 1 MANA e posso invocar uma segunda carta neste turno

  Cenário: MANA insuficiente para o custo da carta
    Dado que tenho MANA 1 e a carta custa 3
    Quando invoco face-up
    Então a carta é descartada, meu MANA vai a 0 e perco 2 de LIFE

  Cenário: Invocar sobre carta minha sem combinação
    Dado que há uma carta minha no bloco alvo
    Quando invoco ali
    Então a carta do bloco é descartada e a nova ocupa o bloco

  Cenário: Invocar sobre o Avatar adversário
    Dado que o LIFE do adversário é maior que o Power da carta
    Quando tento invocar sobre o Avatar dele
    Então vejo a recusa; e se o LIFE for menor ou igual ao Power, o ataque é permitido

  Cenário: Cartas que não são SUMMON
    Dado que tenho uma carta do tipo SPELL na mão
    Quando tento invocá-la
    Então vejo "Tipo de carta ainda não implementado (SPELL)."
```

### US24 — Mover cartas e atacar
**Como** jogador, **quero** mover minhas cartas e atacar as do adversário **para que** eu reduza o LIFE dele. — *RF34, RF35, RF37 · UC07, UC08 · Alta*

```gherkin
Funcionalidade: Movimento e combate

  Cenário: Cooldown da invocação
    Dado que invoquei uma carta neste turno
    Quando tento movê-la
    Então vejo "Carta recém-invocada não pode se mover."

  Cenário: Uma movimentação por turno
    Dado que movi uma carta
    Quando tento movê-la de novo
    Então vejo "Esta carta já se moveu neste turno."

  Cenário: Exemplo do documento — atacante Power 10 contra alvo Power 5
    Dado que minha carta tem Power 10 e a do adversário Power 5, sem Shield
    Quando minha carta ataca a dele
    Então a carta dele é destruída
    E o LIFE do dono dela perde 5 (dano excedente)
    E minha carta recebe 5 de Damage e fica com Power efetivo 5
    E minha carta ocupa o bloco da carta destruída

  Cenário: Empate de Power
    Dado que as duas cartas têm Power 5
    Quando uma ataca a outra
    Então as duas são destruídas e nenhum LIFE é alterado

  Cenário: Shield reduz o dano e nunca cura
    Dado que o alvo tem Shield 2 e meu ataque é 3
    Quando ataco
    Então o alvo recebe 1 de dano
    E se o Shield for maior que o ataque, o dano é 0

  Cenário: Atacante mais fraco
    Dado que minha carta tem Power 3 e o alvo Power 10
    Quando ataco
    Então minha carta é destruída
    E meu LIFE perde 7 (excesso do contra-ataque)
    E o alvo fica com 3 de Damage e permanece em seu bloco

  Cenário: Ataque ao Avatar
    Dado que minha carta tem Power 10
    Quando ataco o Avatar adversário
    Então o LIFE dele perde 10 e minha carta não ocupa o bloco do Avatar

  Cenário: Alvo face-down é revelado antes do combate
    Dado que o alvo está virado para baixo
    Quando ataco
    Então o alvo é revelado e seu MANA COST é cobrado antes do dano

  Cenário: MANA GAIN
    Dado que minha carta tem "Ice +2" e ataco uma carta de elemento Ice
    Quando o ataque é resolvido
    Então meu MANA aumenta em 2, no máximo até 6
```

### US25 — Usar skills
**Como** jogador, **quero** usar as skills de minhas cartas **para que** eu tenha opções táticas além do ataque. — *RF38 · UC07 · Média*

```gherkin
Funcionalidade: Skills

  Cenário: Abrir a lista de skills
    Dado que minha carta face-up já está selecionada
    Quando clico nela de novo
    Então abre o pop-up com as skills, custo e descrição

  Cenário: Fire Ball
    Dado que tenho MANA 1 e uma carta com Fire Ball em campo desde o turno anterior
    Quando uso Fire Ball em uma SUMMON adversária face-up
    Então o alvo recebe 2 de dano ignorando Shield e meu MANA vai a 0

  Cenário: Teleport
    Dado que tenho MANA 2
    Quando uso Teleport
    Então a carta pode se mover duas vezes seguidas neste turno, sem atacar

  Cenário: Explosion
    Dado que tenho MANA 3
    Quando uso Explosion
    Então todas as cartas face-up ao redor, inclusive as minhas, recebem 3 de dano
    E um Avatar ao redor perde 3 de LIFE

  Cenário: Restrições
    Quando tento usar skill com a carta virada para baixo, no turno da invocação,
      depois de mover ou atacar, ou pela segunda vez no turno
    Então a skill é recusada com mensagem de erro e o MANA não é gasto
```

### US26 — Ver e inspecionar a arena
**Como** jogador, **quero** ver a arena, as cartas e os destaques de ação **para que** eu decida minhas jogadas com clareza. — *RF40 · UC07 · Média*

```gherkin
Funcionalidade: Interface da arena

  Cenário: Destaque de blocos válidos
    Quando seleciono uma carta da mão
    Então os blocos ao redor do meu Avatar são destacados para invocação

  Cenário: Seleção visível ao adversário sem vazamento
    Quando seleciono uma carta da mão
    Então o adversário vê que há uma carta selecionada mas não vê qual é

  Cenário: Desmarcar com botão direito
    Dado que há uma carta selecionada
    Quando clico com o botão direito
    Então a seleção é removida

  Cenário: Inspecionar
    Quando passo o mouse sobre uma carta visível
    Então vejo nome, tipo, elementos, Power, Shield, custo, MANA GAIN e skills

  Cenário: Descartes
    Quando clico em "Meu descarte" ou "Descarte do adversário"
    Então vejo todas as cartas descartadas
```

### US27 — Terminar a partida e receber a recompensa
**Como** jogador, **quero** que o resultado e as recompensas sejam definidos automaticamente **para que** meu progresso seja registrado. — *RF42, RF47, RF48 · UC10 · Alta*

```gherkin
Funcionalidade: Fim de partida e recompensas

  Cenário: Vitória por LIFE
    Dado que o LIFE do adversário chega a 0 ou menos
    Então venço; recebo +100 Battlepoints e +1 vitória, e o adversário +50 Battlepoints

  Cenário: Empate
    Dado que os dois LIFE chegam a 0 ou menos na mesma ação
    Então a partida termina em empate e cada um recebe +25 Battlepoints

  Cenário: Magicdust
    Dado que destruí 4 cartas durante a partida
    Então recebo +4 Magicdust

  Cenário: Histórico gravado
    Quando a partida termina
    Então o histórico (modo, jogadores, resultado, motivo, turnos e eventos em ordem) é gravado

  Cenário: Voltar à sala
    Quando fecho o resultado
    Então volto à sala com os READY zerados
```

### US28 — Perder por inatividade
**Como** jogador, **quero** que um adversário ausente perca a partida **para que** eu não fique esperando indefinidamente. — *RF43 · UC07, UC10 · Média*

```gherkin
Funcionalidade: AFK

  Cenário: Três turnos sem ação
    Dado que meu adversário deixou o tempo esgotar nos 3 últimos turnos dele sem nenhuma ação
    Então ele perde por inatividade; recebo 10 Battlepoints e ele 0

  Cenário: Agir zera o contador
    Dado que ele deixou 2 turnos esgotarem
    Quando ele faz qualquer ação no turno seguinte
    Então o contador volta a zero

  Cenário: Encerrar o turno manualmente conta como ação
    Quando o jogador clica em "Encerrar turno" sem outra ação
    Então o turno conta como ação e o contador de AFK é zerado

  Cenário: Modo Debug não perde por AFK
    Dado que a partida é no modo Debug
    Quando o tempo esgota diversas vezes
    Então ninguém perde por AFK
```

### US29 — Voltar à partida após uma queda
**Como** jogador, **quero** reconectar à partida em andamento **para que** uma queda de internet não me faça perder na hora. — *RF45 · UC09 · Média*

```gherkin
Funcionalidade: Reconexão

  Cenário: Reconectar dentro da janela
    Dado que minha conexão caiu durante a partida
    Quando reconecto em menos de 120 segundos
    Então vejo o estado atual da partida
    E o adversário vê "O adversário reconectou."

  Cenário: Aviso ao adversário
    Quando minha conexão cai
    Então o adversário vê "O adversário desconectou. Aguardando reconexão (120 s)."

  Cenário: Janela expirada
    Quando 120 segundos passam sem reconexão
    Então perco por desconexão sem Battlepoints e o adversário recebe 10

  Cenário: Os timers continuam
    Quando estou desconectado
    Então o relógio do turno continua e turnos sem ação contam para o AFK
```

### US30 — Testar sozinho no modo Debug
**Como** jogador (ou desenvolvedor), **quero** controlar os dois lados em uma sala Debug **para que** eu teste cartas e regras sem precisar de adversário. — *RF46 · UC06 · Média*

```gherkin
Funcionalidade: Modo Debug

  Cenário: Início imediato
    Dado que criei uma sala Debug
    Quando clico em READY
    Então a partida inicia sem escolha de X/O

  Cenário: Controle dos dois lados
    Quando é o turno do lado B
    Então eu posso jogar as ações do lado B e vejo as mãos dos dois lados

  Cenário: Sem recompensas
    Quando a partida Debug termina
    Então nenhum Battlepoint, Magicdust ou vitória é concedido, mas o histórico é gravado
```

---

## Épico 5 — Administração e operação

### US31 — Gerenciar o catálogo de cartas
**Como** administrador, **quero** criar, editar, remover, importar e exportar cartas **para que** eu evolua o conteúdo sem mexer no código. — *RF49–RF51 · UC11 · Alta*

```gherkin
Funcionalidade: Administração de cartas

  Cenário: Importação com relatório
    Dado um arquivo CSV com 10 cartas válidas, 1 com Card_ID 0 e 1 repetida
    Quando importo o arquivo
    Então 10 cartas são criadas ou atualizadas
    E o relatório lista a linha do Card_ID 0 e a duplicada como erros

  Cenário: Não sobrescrever existentes
    Dado que desmarquei "Sobrescrever"
    Quando importo cartas com Card_ID já existentes
    Então elas aparecem como "ignoradas" e não são alteradas

  Cenário: Carta importada fica disponível no jogo
    Quando importo uma carta nova
    Então ela aparece no catálogo sem reiniciar o servidor

  Cenário: Remover carta em uso
    Dado que a carta está em algum deck
    Quando tento removê-la
    Então vejo "Carta em uso em decks/Grimorium: não pode ser removida."

  Cenário: Exportar
    Quando clico em "Exportar JSON"
    Então baixo o catálogo no mesmo formato aceito na importação
```

### US32 — Gerenciar contas e permissões
**Como** administrador, **quero** editar o perfil, o status premium, os contadores e a senha de uma conta **para que** eu dê suporte e bloqueie abusos. — *RF52, RF06 · UC12 · Média*

```gherkin
Funcionalidade: Administração de contas

  Cenário: Bloquear conta
    Quando altero o perfil de "Jogador9" para "RED"
    Então "Jogador9" não consegue mais fazer login

  Cenário: Redefinir senha
    Quando informo uma nova senha de 6 a 32 caracteres
    Então a senha é gravada como hash

  Cenário: ADMIN não mexe em contas privilegiadas
    Dado que sou "ADMIN"
    Quando tento alterar o perfil de uma conta "DEV" ou conceder "ADMIN"
    Então a alteração é recusada

  Cenário: DEV altera perfis privilegiados
    Dado que sou "DEV"
    Quando promovo uma conta a "ADMIN"
    Então a alteração é salva
```

### US33 — Restringir o painel a administradores
**Como** dono do produto, **quero** que apenas ADMIN e DEV acessem o painel **para que** dados e configurações fiquem protegidos. — *RF06, RNF21 · UC11–UC13 · Alta*

```gherkin
Funcionalidade: Controle de acesso do painel

  Cenário: Jogador comum
    Dado que sou "GREEN"
    Quando abro "/painel/"
    Então recebo acesso negado

  Cenário: Sem sessão
    Dado que não estou logado
    Quando abro "/painel/"
    Então sou redirecionado ao login

  Cenário: Monitor por WebSocket
    Dado que sou "GREEN"
    Quando tento abrir a conexão do monitor
    Então ela é recusada
```

### US34 — Consultar decks, Grimoriums e histórico
**Como** administrador, **quero** consultar decks, Grimoriums e o histórico de partidas **para que** eu investigue reclamações e verifique a integridade. — *RF53 · UC12 · Média*

```gherkin
Funcionalidade: Consultas administrativas

  Cenário: Ver os eventos de uma partida
    Dado que a partida 15 foi concluída
    Quando abro o histórico da partida 15
    Então vejo seus eventos em ordem cronológica, com turno, jogador, tipo e dados

  Cenário: Ver cartas de um deck
    Quando abro um deck no painel
    Então vejo cada cópia com seu identificador, Card_ID, nome, Foil e Shiny
```

### US35 — Monitorar o servidor em tempo real
**Como** administrador, **quero** ver usuários online, salas, partidas e erros recentes **para que** eu detecte problemas antes dos jogadores reclamarem. — *RF55 · UC13 · Média*

```gherkin
Funcionalidade: Monitoramento

  Cenário: Atualização periódica
    Dado que abri o painel inicial
    Então os indicadores são atualizados a cada 2 segundos

  Cenário: Erros recentes
    Quando ocorre um erro registrado no servidor
    Então ele aparece na tabela "Erros recentes" com hora, nível, origem e mensagem

  Cenário: Reconexão do monitor
    Quando a conexão do monitor cai
    Então a página tenta reconectar automaticamente
```

### US36 — Configurar servidores e manter o chat
**Como** administrador, **quero** ativar ou desativar servidores e apagar mensagens antigas **para que** eu opere o ambiente sem acesso direto ao banco. — *RF54 · Baixa*

```gherkin
Funcionalidade: Configurações

  Cenário: Desativar servidor
    Quando desativo o "Servidor 2"
    Então ele deixa de aparecer na seleção de servidores

  Cenário: Limpeza de chat
    Quando clico em "Apagar mensagens de chat antigas"
    Então as mensagens além do período de retenção são removidas e vejo a quantidade apagada
```

---

## Épico 6 — Qualidade transversal

### US37 — Proteção de informação oculta e trapaça
**Como** jogador, **quero** que o servidor decida todas as regras e esconda a informação do adversário **para que** ninguém trapaceie. — *RNF16, RNF17*

```gherkin
Funcionalidade: Servidor autoritativo

  Cenário: Cliente não escolhe quem age
    Quando um cliente envia um comando com "player" de outro jogador
    Então o servidor ignora o campo e usa o jogador da conexão

  Cenário: Cartas viradas para baixo
    Quando o adversário joga uma carta face-down
    Então meu navegador recebe a carta sem Card_ID, nome ou atributos

  Cenário: Ação inválida não altera o estado
    Quando envio uma ação que viola uma regra
    Então recebo uma mensagem de erro e o estado da partida permanece idêntico
```

### US38 — Extensibilidade por dados
**Como** desenvolvedor, **quero** adicionar skills, combinações e idiomas sem alterar o motor **para que** o jogo cresça com baixo risco. — *RNF28, RNF29, RF39, RF56*

```gherkin
Funcionalidade: Extensibilidade

  Cenário: Nova combinação cadastrada por dados
    Dado que cadastrei uma combinação "Fire + Ice"
    Quando movo uma carta Fire sobre uma carta Ice minha
    Então o efeito da combinação é aplicado sem alteração de código

  Cenário: Sem combinação cadastrada
    Quando movo uma carta minha sobre outra carta minha sem combinação
    Então o movimento é bloqueado com "Sem combinação cadastrada para este movimento."

  Cenário: Novo idioma
    Dado que criei "locale/en_US/messages.json" e defini IDIOMA=EN-US
    Então a interface passa a usar os textos do novo idioma, com fallback para PT-BR
```

---

## Matriz de rastreabilidade História × Requisito

| História | Requisitos | Caso de uso |
|---|---|---|
| US01–US02 | RF01, RF02, RF07 | UC01 |
| US03–US04 | RF03–RF06 | UC02 |
| US05 | RF08 | — |
| US06–US07 | RF09, RF10 | UC05 |
| US08–US09, US14 | RF11, RF12, RF17 | UC04 |
| US10–US13 | RF13–RF16, RF18, RF19 | UC05 |
| US15–US17 | RF20–RF23 | UC03 |
| US18–US20 | RF24–RF27 | UC06 |
| US21–US26 | RF28–RF41 | UC07, UC08 |
| US27–US28 | RF42–RF44, RF47, RF48 | UC10 |
| US29 | RF45 | UC09 |
| US30 | RF46 | UC06 |
| US31–US36 | RF49–RF55 | UC11–UC13 |
| US37–US38 | RNF16, RNF17, RNF28, RNF29, RF39, RF56 | — |

import type { EngineInterface, Register, ThemeResult, ThemeSetArgs } from 'claude-code'
import { makeColors } from './make-colors.js'
import { CENAS } from './cenas.js'
import { ORDEM, PADRAO, TEMAS, type NomeTema } from './definicoes.js'

type Visual = { visual: ThemeSetArgs; recusa: string | undefined }

// Monta uma vez o visual inteiro de cada fundo: as cores pelo makeColors e a cena animada.
// `recusa` guarda a linha do makeColors que faria o Desktop ignorar as cores, se houver.
const VISUAIS = Object.fromEntries(
  ORDEM.map(nome => {
    const tema = TEMAS[nome]
    const { theme, problems } = makeColors(tema.cores)
    const visual: ThemeSetArgs = { colors: theme, backdrop: { scene: nome, glass: tema.vidro } }
    const recusa = problems.find(linha => linha.startsWith("Desktop won't paint"))
    return [nome, { visual, recusa }]
  }),
) as Record<NomeTema, Visual>

type Pedido = NomeTema | 'desligar' | 'proximo'

// O que a pessoa pode escrever depois de /fundo.
const APELIDOS: Record<string, Pedido> = {
  aurora: 'aurora',
  boreal: 'aurora',
  'aurora-boreal': 'aurora',
  neon: 'neon',
  neon84: 'neon',
  'neon-84': 'neon',
  '84': 'neon',
  synthwave: 'neon',
  retro: 'neon',
  sertao: 'sertao',
  'sertão': 'sertao',
  entardecer: 'sertao',
  caatinga: 'sertao',
  cerrado: 'cerrado',
  ipe: 'cerrado',
  'ipê': 'cerrado',
  buriti: 'cerrado',
  vereda: 'cerrado',
  manha: 'cerrado',
  'manhã': 'cerrado',
  desligar: 'desligar',
  desliga: 'desligar',
  off: 'desligar',
  nenhum: 'desligar',
  sem: 'desligar',
  limpar: 'desligar',
  proximo: 'proximo',
  'próximo': 'proximo',
  outro: 'proximo',
  next: 'proximo',
}

// A escolha fica guardada em $.store('tema'): um NomeTema, ou 'desligado'. Sem nada guardado, vale o PADRAO.
const DESLIGADO = 'desligado'

function ehTema(valor: unknown): valor is NomeTema {
  return typeof valor === 'string' && (ORDEM as readonly string[]).includes(valor)
}

function emUso(guardado: unknown): NomeTema | undefined {
  if (guardado === DESLIGADO) {
    return undefined
  }
  return ehTema(guardado) ? guardado : PADRAO
}

function seguinte(guardado: unknown): NomeTema {
  const atual = emUso(guardado)
  if (atual === undefined) {
    return PADRAO
  }
  return ORDEM[(ORDEM.indexOf(atual) + 1) % ORDEM.length] ?? PADRAO
}

function lista(guardado: unknown): string {
  const atual = emUso(guardado)
  const linhas = ORDEM.map(nome => {
    const marca = nome === atual ? '●' : '○'
    return `${marca} /fundo ${nome}: ${TEMAS[nome].titulo}. ${TEMAS[nome].descricao}`
  })
  return [
    atual === undefined ? 'Fundos animados (agora: desligado):' : `Fundos animados (agora: ${TEMAS[atual].titulo}):`,
    ...linhas,
    '/fundo proximo: passa para o seguinte.',
    '/fundo desligar: volta ao visual normal do app.',
  ].join('\n')
}

async function aplicar($: EngineInterface, nome: NomeTema): Promise<ThemeResult> {
  const { visual, recusa } = VISUAIS[nome]
  if (recusa !== undefined) {
    $.ui.toast(recusa)
  }
  return $.theme.set(visual)
}

// Guarda em $.store('ultimo') o que aconteceu na última vez que um app de verdade pediu o fundo,
// para conferir depois sem abrir a janela. Sessão de terminal e `claude -p` não gravam nada.
async function anotar($: EngineInterface, nome: NomeTema, resultado: ThemeResult): Promise<void> {
  const superficies = await $.session.surfaces()
  const noApp = superficies.some(s => s === 'desktop' || s === 'mobile')
  if (!resultado.isDrawn && !noApp) {
    return
  }
  await $.store.set('ultimo', {
    tema: nome,
    desenhado: resultado.isDrawn,
    motivo: resultado.isDrawn ? undefined : resultado.reason,
    superficies,
    quando: new Date().toISOString(),
  })
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    await $.command.register({
      name: 'fundo',
      description: 'Troca o fundo animado do app: aurora, neon, sertao, cerrado ou desligar',
      argumentHint: 'aurora | neon | sertao | cerrado | proximo | desligar',
      immediate: true,
    })
    const nome = emUso(await $.store.get('tema'))
    if (nome !== undefined) {
      const resultado = await aplicar($, nome)
      await anotar($, nome, resultado)
    }
    return next(e)
  })

  // Desenha só as cenas deste mod, e só onde há janela para isso (Desktop e celular).
  on('ui.render', { component: 'Backdrop' }, ($, e, next) => {
    const cena = e.props.scene
    if (e.props.plugin !== $.plugin.name || !ehTema(cena)) {
      return next(e)
    }
    if (e.surface !== 'desktop' && e.surface !== 'mobile') {
      return next(e)
    }
    const { Svg } = $.ui.resolve(e)
    return Svg({ source: CENAS[cena].svg, alt: CENAS[cena].alt, isInteractive: true })
  })

  on('command.run', { command: 'fundo' }, async ($, e) => {
    const escrito = e.args.trim()
    const guardado = await $.store.get('tema')
    if (escrito === '') {
      return { text: lista(guardado) }
    }
    const pedido = APELIDOS[escrito.toLowerCase()]
    if (pedido === undefined) {
      return { text: `Não conheço o fundo "${escrito}".\n\n${lista(guardado)}` }
    }
    if (pedido === 'desligar') {
      await $.store.set('tema', DESLIGADO)
      await $.theme.clear()
      return { text: 'Fundo desligado: o app voltou ao visual normal. Para religar: /fundo aurora, /fundo neon, /fundo sertao ou /fundo cerrado.' }
    }
    const nome = pedido === 'proximo' ? seguinte(guardado) : pedido
    await $.store.set('tema', nome)
    const resultado = await aplicar($, nome)
    await anotar($, nome, resultado)
    const tema = TEMAS[nome]
    if (resultado.isDrawn) {
      return { text: `Fundo trocado para ${tema.titulo}. ${tema.descricao}` }
    }
    return {
      text: `Guardei ${tema.titulo} como fundo. Ele aparece no app Desktop, na aba Code, em sessão local; aqui não aparece (${resultado.reason}).`,
    }
  })
}

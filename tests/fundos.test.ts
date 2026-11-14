import type { On, ThemeResult, ThemeSetArgs } from 'claude-code'
import { describe, expect, test } from 'claude-code/testing'

const PLUGIN = 'fundos-animados'

// O que fica embaixo do mod num app de verdade, imitado: a memória entre sessões, o pedido de fundo,
// a limpeza e as superfícies abertas. `pedidos` guarda cada $.theme.set, `limpezas` conta os $.theme.clear.
function mundo(on: On, opcoes: { desenha: boolean; superficies: ('desktop' | 'terminal')[] }) {
  const memoria = new Map<string, unknown>()
  const pedidos: ThemeSetArgs[] = []
  let limpezas = 0
  const resposta: ThemeResult = opcoes.desenha
    ? { isDrawn: true, requestId: 'fundo-1' }
    : { isDrawn: false, reason: 'nenhum app aberto desenha fundos' }
  on('store.get', (_, e) => ({ value: memoria.get(e.key) }))
  on('store.set', (_, e) => {
    memoria.set(e.key, e.value)
    return { value: undefined }
  })
  on('command.register', (_, e) => ({ value: { command: e.name } }))
  on('session.start', (_, e) => ({ cwd: e.cwd }))
  on('session.surfaces', () => ({ value: opcoes.superficies }))
  on('ui.toast', () => ({ value: undefined }))
  on('theme.set', (_, e) => {
    pedidos.push(e)
    return { value: resposta }
  })
  on('theme.clear', () => {
    limpezas += 1
    return { value: { isDrawn: false, reason: 'limpo' } }
  })
  return { memoria, pedidos, limpezas: () => limpezas }
}

const COMANDO = { origin: { kind: 'composer' }, presentation: { isFullscreen: false, columns: 80 } } as const
const INICIO = { cwd: '/', surface: 'desktop', isInteractive: true } as const

describe('/fundo', () => {
  test('sem escolha guardada, a sessão começa com a Aurora boreal', async ($, on) => {
    const m = mundo(on, { desenha: true, superficies: ['desktop'] })
    await $.session.start(INICIO)
    expect(m.pedidos).toHaveLength(1)
    expect(m.pedidos[0]?.backdrop?.scene).toBe('aurora')
    expect(m.pedidos[0]?.colors?.label).toBe('Aurora boreal')
    expect(m.memoria.get('ultimo')).toMatchObject({ tema: 'aurora', desenhado: true })
  })

  test('/fundo neon troca na hora e vale na sessão seguinte', async ($, on) => {
    const m = mundo(on, { desenha: true, superficies: ['desktop'] })
    await $.session.start(INICIO)
    const r = await $.command.run({ ...COMANDO, command: 'fundo', args: 'neon' })
    expect(r).toMatchObject({ text: expect.stringContaining('Neon 84') })
    expect(m.pedidos.at(-1)?.backdrop?.scene).toBe('neon')
    await $.session.start(INICIO)
    expect(m.pedidos.at(-1)?.backdrop?.scene).toBe('neon')
  })

  test('apelidos e /fundo proximo passam pelos quatro fundos em ordem', async ($, on) => {
    const m = mundo(on, { desenha: true, superficies: ['desktop'] })
    await $.command.run({ ...COMANDO, command: 'fundo', args: 'Sertão' })
    expect(m.pedidos.at(-1)?.backdrop?.scene).toBe('sertao')
    await $.command.run({ ...COMANDO, command: 'fundo', args: 'proximo' })
    expect(m.pedidos.at(-1)?.backdrop?.scene).toBe('cerrado')
    await $.command.run({ ...COMANDO, command: 'fundo', args: 'proximo' })
    expect(m.pedidos.at(-1)?.backdrop?.scene).toBe('aurora')
    await $.command.run({ ...COMANDO, command: 'fundo', args: 'próximo' })
    expect(m.pedidos.at(-1)?.backdrop?.scene).toBe('neon')
  })

  test('/fundo desligar limpa e a sessão seguinte não põe fundo nenhum', async ($, on) => {
    const m = mundo(on, { desenha: true, superficies: ['desktop'] })
    await $.session.start(INICIO)
    const r = await $.command.run({ ...COMANDO, command: 'fundo', args: 'desligar' })
    expect(r).toMatchObject({ text: expect.stringContaining('Fundo desligado') })
    expect(m.limpezas()).toBe(1)
    const antes = m.pedidos.length
    await $.session.start(INICIO)
    expect(m.pedidos).toHaveLength(antes)
  })

  test('sem nada escrito lista os fundos; nome desconhecido lista e não troca', async ($, on) => {
    const m = mundo(on, { desenha: true, superficies: ['desktop'] })
    const lista = await $.command.run({ ...COMANDO, command: 'fundo', args: '' })
    expect(lista).toMatchObject({ text: expect.stringContaining('● /fundo aurora') })
    const errado = await $.command.run({ ...COMANDO, command: 'fundo', args: 'praia' })
    expect(errado).toMatchObject({ text: expect.stringContaining('Não conheço o fundo "praia"') })
    expect(m.pedidos).toHaveLength(0)
  })

  test('no terminal a escolha fica guardada, avisa onde aparece e não grava diagnóstico', async ($, on) => {
    const m = mundo(on, { desenha: false, superficies: ['terminal'] })
    const r = await $.command.run({ ...COMANDO, command: 'fundo', args: 'sertao' })
    expect(r).toMatchObject({ text: expect.stringContaining('aqui não aparece (nenhum app aberto desenha fundos)') })
    expect(m.memoria.get('tema')).toBe('sertao')
    expect(m.memoria.has('ultimo')).toBe(false)
  })
})

describe('as cenas', () => {
  for (const cena of ['aurora', 'neon', 'sertao', 'cerrado'] as const) {
    test(`${cena} desenha a cena animada no Desktop e no celular`, async $ => {
      for (const surface of ['desktop', 'mobile'] as const) {
        const ui = await $.ui.mount({
          plugin: PLUGIN,
          surface,
          component: 'Backdrop',
          props: { scene: cena, plugin: PLUGIN, glass: { blur: 16, opacity: 0.55 } },
        })
        const svg = await ui.find({ type: 'Svg' })
        expect(String(svg?.props.source)).toContain('<svg')
        expect(String(svg?.props.source)).toContain('@keyframes')
        expect(String(svg?.props.alt).length).toBeGreaterThan(20)
        await ui.unmount()
      }
    })
  }

  test('o fundo de outro mod fica com quem o pediu', async $ => {
    const ui = await $.ui.mount({
      plugin: PLUGIN,
      surface: 'desktop',
      component: 'Backdrop',
      props: { scene: 'aurora', plugin: 'outro-mod', glass: false },
    })
    expect(await ui.find({ type: 'Svg', text: /aurora/i })).toBeUndefined()
    await ui.unmount()
  })
})

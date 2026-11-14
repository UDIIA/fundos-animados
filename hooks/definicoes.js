// definicoes.js: os quatro fundos do mod, com o nome, a descrição, as cores e o vidro de cada um.
// As cores passam pelo makeColors (make-colors.js) em register.ts; aqui ficam só as sementes.
// Os ajustes de superfície-3, cinza 0, git e papéis por modo zeram os avisos de contraste do makeColors
// (conferido com tmp/confere_cores.mjs em 13/11/2026): sem eles, diff e bordas ficavam apagados.

/** A ordem em que /fundo lista e alterna os fundos. */
export const ORDEM = ['aurora', 'neon', 'sertao', 'cerrado']

/** O fundo que entra quando a pessoa ainda não escolheu nenhum. */
export const PADRAO = 'aurora'

export const TEMAS = {
  aurora: {
    titulo: 'Aurora boreal',
    descricao: 'Céu de inverno com cortinas de aurora verde e violeta, estrelas cadentes e montanhas com pinheiros.',
    vidro: { blur: 18, opacity: 0.55 },
    cores: {
      label: 'Aurora boreal',
      only: 'dark',
      roles: { accent: '#3ff0b9', danger: '#ff7a8a', success: '#a6e35a', warning: '#ffcc66', pro: '#b794ff' },
      dark: {
        gray: {
          anchors: {
            'surface-0': '#0a0f1c',
            'surface-1': '#0f1626',
            'surface-2': '#141c2f',
            'surface-3': '#192136',
            'text-primary': '#e6f1ff',
            'text-secondary': '#b8c7dd',
            'text-muted': '#8a9bb5',
          },
        },
      },
    },
  },
  neon: {
    titulo: 'Neon 84',
    descricao: 'Sol listrado no horizonte, montanhas com contorno neon, palmeiras e uma grade de luz correndo no chão.',
    vidro: { blur: 16, opacity: 0.55 },
    cores: {
      label: 'Neon 84',
      only: 'dark',
      roles: { accent: '#ff4fa3', danger: '#ff6b5a', success: '#39f0a0', warning: '#ffb547', pro: '#3ee6ff' },
      dark: {
        gray: {
          anchors: {
            'surface-0': '#120a1f',
            'surface-1': '#1a0f2b',
            'surface-2': '#211436',
            'surface-3': '#251a37',
            'text-primary': '#fbe9ff',
            'text-secondary': '#d9bfe6',
            'text-muted': '#a98bbd',
          },
          stops: { 0: '#ffffff' },
        },
      },
    },
  },
  sertao: {
    titulo: 'Sertão ao entardecer',
    descricao: 'Sol se pondo atrás da chapada, mandacarus, um cata-vento girando, pássaros de passagem e vaga-lumes.',
    vidro: { blur: 16, opacity: 0.6 },
    cores: {
      label: 'Sertão ao entardecer',
      roles: { accent: '#d2662e', danger: '#b8323f', success: '#5f8f3a', warning: '#d9a21b', pro: '#8b5fbf' },
      light: {
        gray: {
          anchors: {
            'surface-0': '#f3e3cf',
            'surface-1': '#f7ecdd',
            'surface-2': '#fbf4ea',
            'text-primary': '#0b0705',
            'text-secondary': '#5a4330',
            'text-muted': '#6e5541',
          },
        },
        roles: { warning: { seed: '#d9a21b', fillShade: 250 } },
        git: {
          added: '#1b8e36',
          removed: '#b91d4c',
          modified: '#89731c',
          merged: '#8060c3',
          closed: '#ec362c',
          conflicting: '#b15818',
          draft: '#656565',
        },
      },
      dark: {
        gray: {
          anchors: {
            'surface-0': '#1c120d',
            'surface-1': '#251812',
            'surface-2': '#2e1e16',
            'surface-3': '#35231a',
            'text-primary': '#f8ebde',
            'text-secondary': '#d8c0a8',
            'text-muted': '#b09780',
          },
          stops: { 0: '#ffffff' },
        },
        roles: { success: { seed: '#5f8f3a', stops: { 400: '#6c9c46' } } },
        git: { removed: '#ff5678', merged: '#bc9eff', closed: '#ff7972', conflicting: '#fb9348', draft: '#adadad' },
      },
    },
  },
  cerrado: {
    titulo: 'Cerrado de manhã',
    descricao: 'Sol nascendo atrás da chapada, ipê-amarelo soltando flores, buritis na vereda, capim dourado balançando e araras voando.',
    vidro: { blur: 16, opacity: 0.6 },
    cores: {
      label: 'Cerrado de manhã',
      roles: { accent: '#3f7a2e', danger: '#b8323f', success: '#4f8a34', warning: '#d9a21b', pro: '#2f6fc0' },
      light: {
        gray: {
          anchors: {
            'surface-0': '#f3e6cc',
            'surface-1': '#f7eedc',
            'surface-2': '#fbf5ea',
            'text-primary': '#070803',
            'text-secondary': '#4a4630',
            'text-muted': '#5f5a40',
          },
        },
        roles: { warning: { seed: '#d9a21b', fillShade: 250 } },
        git: {
          added: '#1b8e36',
          removed: '#b91d4c',
          modified: '#89731c',
          merged: '#8060c3',
          closed: '#ec362c',
          conflicting: '#b15818',
          draft: '#656565',
        },
      },
      dark: {
        gray: {
          anchors: {
            'surface-0': '#14170f',
            'surface-1': '#1b1f15',
            'surface-2': '#22271b',
            'surface-3': '#24291d',
            'text-primary': '#eef0e0',
            'text-secondary': '#cdd0b4',
            'text-muted': '#a6aa8c',
          },
          stops: { 0: '#ffffff' },
        },
        roles: { accent: { seed: '#3f7a2e', stops: { 400: '#5f9c48' } }, success: { seed: '#4f8a34', stops: { 400: '#68a24a' } } },
        git: { removed: '#ff5678', merged: '#bc9eff', closed: '#ff7972', conflicting: '#fb9348', draft: '#b8b8b8' },
      },
    },
  },
}

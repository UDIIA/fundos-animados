import type { NomeTema } from './definicoes.js'

/** Uma cena animada: o SVG inteiro e a descrição para quem não vê a imagem. */
export type Cena = { svg: string; alt: string }

export declare const CENAS: Record<NomeTema, Cena>

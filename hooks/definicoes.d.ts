import type { ThemeBackdropGlass } from 'claude-code'
import type { makeColors } from './make-colors.js'

export type NomeTema = 'aurora' | 'neon' | 'sertao' | 'cerrado'

export type Tema = {
  /** O nome que /fundo mostra. */
  titulo: string
  /** Uma frase sobre a cena. */
  descricao: string
  /** As sementes de cor que o makeColors transforma no tema inteiro. */
  cores: Parameters<typeof makeColors>[0]
  /** Quanto o app embaça e cobre a cena atrás dos painéis. */
  vidro: ThemeBackdropGlass
}

export declare const ORDEM: readonly NomeTema[]
export declare const PADRAO: NomeTema
export declare const TEMAS: Record<NomeTema, Tema>

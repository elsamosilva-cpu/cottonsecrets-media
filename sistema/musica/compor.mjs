// Musica original, suave e acolhedora — DIFERENTE para cada Reel (semente aleatoria).
// Varia: tonalidade, progressao, andamento, instrumento principal, padrao de arpejo, pad e melodia.
// Uso: node compor.mjs <saida.mid> <semente> <duracao_segundos>
import fs from "node:fs";
import MidiWriter from "midi-writer-js";

const [out, seedArg, durArg] = process.argv.slice(2);
let s = (Number(seedArg) * 2654435761) % 2147483648 || 1;
const rnd = () => ((s = (s * 1103515245 + 12345) % 2147483648) / 2147483648);
const pick = a => a[Math.floor(rnd() * a.length)];
for (let i = 0; i < 7; i++) rnd();

const NOTES = ["C","Db","D","Eb","E","F","Gb","G","Ab","A","Bb","B"];
const name = m => NOTES[m % 12] + (Math.floor(m / 12) - 1);
const key = pick([0, 2, 3, 5, 7, 8, 10]) + 48;              // C D Eb F G Ab Bb (oitava 3)
const MAJ = [0, 2, 4, 5, 7, 9, 11];
// graus (0=I) — progressoes suaves
const prog = pick([[0,5,3,4],[0,3,5,4],[3,4,0,5],[0,4,5,3],[5,3,0,4],[0,2,3,4],[3,0,4,5],[0,5,1,4]]);
const tempo = pick([66, 70, 74, 78, 82]);
const lead = pick([0, 1, 4, 46, 10, 11, 24]);  // piano, piano brilhante, piano eletrico, harpa, caixa de musica, vibrafone, guitarra nylon
const padI = pick([48, 49, 89, 88, 52, 91]);   // cordas, cordas lentas, pad quente, new age, coro, pad coral
const bassI = pick([32, 33, 0]);
const pattern = pick([[0,2,1,3,4,3,2,1],[0,1,2,3,2,1,2,3],[0,2,3,4,3,2,1,2],[0,3,2,4,1,3,2,4],[0,2,4,2,1,3,4,3]]);
const swing = pick([0, 0, 6]);

const chord = d => [0, 2, 4, 6].map(i => {          // acorde de setima diatonico
  const k = d + i; return key + MAJ[k % 7] + 12 * Math.floor(k / 7);
});
const TPB = 128, BAR = TPB * 4, E = TPB / 2;
const dur = Number(durArg) || 30;
const nBars = Math.ceil(dur / (240 / tempo)) + 1;

const t1 = new MidiWriter.Track(), t2 = new MidiWriter.Track(), t3 = new MidiWriter.Track();
t1.setTempo(tempo);
t1.addEvent(new MidiWriter.ProgramChangeEvent({ instrument: lead, channel: 1 }));
t2.addEvent(new MidiWriter.ProgramChangeEvent({ instrument: padI, channel: 2 }));
t3.addEvent(new MidiWriter.ProgramChangeEvent({ instrument: bassI, channel: 3 }));

// melodia: motivo de 2 compassos gerado e repetido com variacao
const scale = [...Array(10)].map((_, i) => key + 12 + MAJ[i % 7] + 12 * Math.floor(i / 7));
const motif = [...Array(6)].map(() => ({ st: pick([0, 2, 3, 4, 6]), len: pick([2, 2, 3, 4]), n: pick([2, 3, 4, 5, 6, 7]) }));
const melStart = pick([2, 4]);

for (let b = 0; b < nBars; b++) {
  const last = b === nBars - 1;
  const deg = prog[b % prog.length];
  const ch = chord(deg), t0 = b * BAR;
  const tones = [...ch, ch[0] + 12, ch[1] + 12];
  pattern.forEach((pi, i) => {
    if (last && i > 3) return;
    const sw = i % 2 ? swing : 0;
    t1.addEvent(new MidiWriter.NoteEvent({ pitch: [name(tones[pi])], tick: t0 + i * E + sw,
      duration: "T" + (last ? BAR * 2 : E * 2), velocity: 32 + Math.floor(rnd() * 14), channel: 1 }));
  });
  t2.addEvent(new MidiWriter.NoteEvent({ pitch: ch.map(m => name(m + 12)), tick: t0,
    duration: "T" + (last ? BAR * 2 : BAR), velocity: 24, channel: 2 }));
  t3.addEvent(new MidiWriter.NoteEvent({ pitch: [name(ch[0] - 12)], tick: t0,
    duration: "T" + (last ? BAR * 2 : BAR), velocity: 36, channel: 3 }));
  // melodia a partir de melStart, em blocos de 2 compassos
  if (b >= melStart && !last) {
    const half = (b - melStart) % 2;
    motif.slice(half * 3, half * 3 + 3).forEach(({ st, len, n }) => {
      const varied = scale[Math.min(9, n + (b % 4 === 3 ? 1 : 0))];
      t1.addEvent(new MidiWriter.NoteEvent({ pitch: [name(varied)], tick: t0 + st * E,
        duration: "T" + len * E, velocity: 50, channel: 1 }));
    });
  }
}
fs.writeFileSync(out, Buffer.from(new MidiWriter.Writer([t1, t2, t3]).buildFile()));
console.log(JSON.stringify({ seed: seedArg, key: NOTES[key % 12], tempo, lead, pad: padI, prog }));

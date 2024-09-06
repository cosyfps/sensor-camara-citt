import { formatHoraEntrada } from "../logic/formatTime"
import { entryClass } from "../types/types"

export const ListaPersonas = ({cards}: {cards: entryClass[] | undefined}) => {
   return <aside className='sm:[grid-area:sidelist] w-[350px] overflow-y-auto items-center flex justify-start flex-col bg-sky-600'>
    <h1> LISTA DE PERSONAS </h1>
      <ul className='cards flex flex-col gap-3 mt-3'>
        {
        cards != undefined ?
          cards.map((card) => (
            <div key={card.id} className='p-4 card rounded-none flex justify-center bg-teal-400 h-[80px] text-primary-content w-[300px]'>
              <p>Persona {card.id} ha entrado</p>
              <p>{formatHoraEntrada(card.timestamp.toString())}</p>
            </div>
          )): <div>No hay datos</div>
         }
    </ul>
  </aside>
}
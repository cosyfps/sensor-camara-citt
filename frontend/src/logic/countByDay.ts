import { entryClass } from "../types/types";

export const countEntriesByDay = (cards: entryClass[] | undefined) => {

   const optionsDay: Intl.DateTimeFormatOptions = { 
    weekday: "long", 
    timeZone: "America/Santiago"
    };

    const days = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes'] as const;
    const entryCount: Record<typeof days[number], number> = {
      Lunes: 0,
      Martes: 0,
      Miércoles: 0,
      Jueves: 0,
      Viernes: 0
    };

    if(cards != undefined){
      cards.forEach(card => {
        const date = new Date(card.timestamp);
        const dayOfWeek = new Intl.DateTimeFormat("es-CL", optionsDay).format(date);
        switch (dayOfWeek) {
          case "lunes":
            entryCount.Lunes++;
            break;
          case "martes":
            entryCount.Martes++;
            break;
          case "miércoles":
            entryCount.Miércoles++;
            break;
          case "jueves":
            entryCount.Jueves++;
            break;
          case "viernes":
            entryCount.Viernes++;
            break;
          default:
            break;
        }
      });
      return days.map(day => entryCount[day]);
    }

    return
  };
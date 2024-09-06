//import { useState } from 'react'
import { useEffect, useState } from 'react';
import './App.css'
import Chart from 'chart.js/auto';
import { countEntriesByDay } from './logic/countByDay';
import { entryClass } from './types/types';
import { ListaPersonas } from './components/List';




function App() {


  const [cards, setCard] = useState<entryClass[] | undefined>()

  useEffect(() => {
    const fetchData = () => fetch('http://localhost:5000/traffic_counts')  // URL de tu API Flask
      .then(response => response.json())
      .then(data => setCard(data))
      .catch(error => console.error('Error fetching traffic counts:', error));

    fetchData();

    let intervalId = setInterval(fetchData, 5000)

    clearInterval(intervalId)

  }, []);

  useEffect(() => {
    
    const ctx = document.getElementById('myChart')! as HTMLCanvasElement;
    ctx.getContext('2d')
    const dataForChart = countEntriesByDay(cards);

    if (ctx !== null) {
      let myCanvas = new Chart(ctx, {
        type: 'bar',
        data: {
          labels: ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes'],
          datasets: [{
            label: 'Cantidad de entradas durante el día',
            data: dataForChart,
            borderWidth: 1
          }]
        },
        options: {
          maintainAspectRatio: false,
          scales: {
            y: {
              stacked: true,
              grid:{
                display:true
              },
              
            },
            x: {
              grid: {
                display: false
              }
            }
          }
        }
      })
      return () => {
        myCanvas.destroy()
      }
    }

  }, [cards])

  return (
    <>

      <ListaPersonas cards={cards}/>

      <section className='flex-col justify-start m-auto flex'>
        {/* <main className='stats sm:[grid-area:counter] justify-center items-center flex-col flex border-solid w-[250px] h-[130px] bg-orange-500'> */}
          {/* <div className="stat-title text-white font-bold">Cantidad actual de personas</div> */}
          {/* <div className="stat-value text-white border-none"></div> */}
        {/* </main> */}
       <div className='sm:[grid-area:graph] relative m-auto h-[300px] sm:h-[400px] w-[70vw] sm:w-[60vw]'>
          <canvas id='myChart' className='bg-white'></canvas>
       </div>
      </section>
    </>
  )
}


export default App

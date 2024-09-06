export const formatHoraEntrada = (hora: string) => {
    const fecha = new Date(hora);
    return fecha.toLocaleString('es-CL', {
      weekday: 'long',
      year: 'numeric',
      month: 'numeric',
      day: 'numeric',
      hour: 'numeric',
      minute: 'numeric',
      hour12: true,
      timeZone: 'America/Santiago',
    });
  };
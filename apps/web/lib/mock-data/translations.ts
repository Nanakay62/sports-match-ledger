export interface LocalizedEventData {
  headline: string;
  summary: string;
  statusNote?: string;
}

export interface LocalizedClaimData {
  text: string;
}

export const EVENT_TRANSLATIONS: Record<string, Record<string, LocalizedEventData>> = {
  "e-001-osei-arsenal": {
    it: {
      headline: "Emeka Osei completa il passaggio da 64 milioni di euro all'Arsenal dallo Sporting CP",
      summary: "Annunciato da entrambi i club martedì pomeriggio; cifra confermata nel deposito federale. Contratto quinquennale fino al 2030 con 6 milioni di bonus.",
    },
    es: {
      headline: "Emeka Osei completa su traspaso de 64 millones de euros al Arsenal procedente del Sporting CP",
      summary: "Anunciado por ambos clubes el martes por la tarde; la cifra se confirma en el registro de la liga. Contrato de cinco años hasta 2030 con 6 millones en variables.",
    },
    de: {
      headline: "Emeka Osei wechselt für 64 Mio. Euro von Sporting CP zu Arsenal",
      summary: "Am Dienstagnachmittag von beiden Klubs bekanntgegeben; die Ablösesumme ist offiziell im Liga-Register hinterlegt. Fünfjahresvertrag bis 2030 mit 6 Mio. Euro Bonuszahlungen.",
    },
    fr: {
      headline: "Emeka Osei rejoint Arsenal en provenance du Sporting CP pour 64 millions d'euros",
      summary: "Officialisé par les deux clubs mardi après-midi ; montant confirmé auprès de la ligue. Contrat de cinq ans jusqu'en 2030 assorti de 6 millions d'euros de bonus.",
    },
  },
  "e-005-barski-barca": {
    it: {
      headline: "Barcellona e Viktor Barski: accordo sui termini personali o nessuna intesa?",
      summary: "Notizia smentita dopo contraddizioni documentali; le fonti del club confermano che nessuna scheda d'accordo è stata approvata.",
      statusNote: "Accordo smentito dopo prove discordanti e presa di posizione del club.",
    },
    es: {
      headline: "Barcelona y Viktor Barski: ¿acuerdo en términos personales o ningún avance?",
      summary: "Afirmación corregida tras contradicciones documentadas; fuentes oficiales del club aseguran que no existe hoja de términos acordada.",
      statusNote: "Afirmación retractada tras desmentido oficial del club.",
    },
    de: {
      headline: "FC Barcelona und Viktor Barski: Persönliche Einigung erzielt oder reine Erfindung?",
      summary: "Bericht nach dokumentierten Widersprüchen korrigiert; Vereinsquellen bestätigen, dass kein Entwurf vorliegt.",
      statusNote: "Meldung nach offiziellem Vereinsdementi korrigiert.",
    },
    fr: {
      headline: "Barcelone et Viktor Barski : termes personnels conclus ou absence totale d'accord ?",
      summary: "Information rectifiée suite à des contradictions documentées ; les sources du club assurent qu'aucun accord n'a été transmis.",
      statusNote: "Information retirée suite au démenti officiel du club.",
    },
  },
  "e-011-sy-newcastle": {
    it: {
      headline: "Il Newcastle offre 45 milioni di sterline per Amadou Sy: ma il club venditore nega offerte",
      summary: "Indiscrezione di un'offerta formale contestata apertamente dalla dirigenza del club venditore, che smentisce contatti formali.",
      statusNote: "Dichiarazione contestata a seguito di smentita esplicita del club venditore.",
    },
    es: {
      headline: "El Newcastle presenta 45 millones de libras por Amadou Sy: pero el club vendedor afirma que no llegó ninguna oferta",
      summary: "Rumor de una oferta formal disputado abiertamente por la directiva del club vendedor, que asegura no haber recibido propuesta.",
      statusNote: "Afirmación disputada tras desmentido categórico del club vendedor.",
    },
    de: {
      headline: "Newcastle legt 45 Mio. Pfund für Amadou Sy vor: Doch der abgebende Klub dementiert jedes Angebot",
      summary: "Meldung über ein formelles Angebot wird von der Vereinsführung des abgebenden Klubs ausdrücklich bestritten.",
      statusNote: "Aussage nach ausdrücklichem Dementi als bestritten eingestuft.",
    },
    fr: {
      headline: "Newcastle transmet 45M£ pour Amadou Sy : mais le club vendeur affirme n'avoir reçu aucune offre",
      summary: "Rumeur d'une offre formelle contestée ouvertement par les dirigeants vendeurs, qui démentent toute proposition reçue.",
      statusNote: "Allégation contestée à la suite du démenti du club vendeur.",
    },
  },
};

export const CLAIM_TRANSLATIONS: Record<string, Record<string, LocalizedClaimData>> = {
  "c-005a": {
    it: { text: "Nessuna scheda contrattuale è stata scambiata tra il Barcellona e l'entourage di Barski. Ogni colloquio finora è stato informale." },
    es: { text: "No se ha intercambiado ninguna propuesta contractual entre el Barcelona y los representantes de Barski. Todo ha sido informal." },
    de: { text: "Zwischen dem FC Barcelona und der Spielerseite von Barski wurde kein Dokument ausgetauscht. Alle bisherigen Kontakte waren unverbindlich." },
    fr: { text: "Aucun document contractuel n'a été échangé entre Barcelone et les représentants de Barski. Les discussions à ce jour restent informelles." },
  },
  "c-005b": {
    it: { text: "Barcellona ha concordato i termini personali con Viktor Barski su un contratto quinquennale; restano da definire i dettagli con il club." },
    es: { text: "El Barcelona ha acordado los términos personales con Viktor Barski en un contrato de cinco años; faltan los flecos con el club." },
    de: { text: "Der FC Barcelona hat mit Viktor Barski eine persönliche Einigung über einen Fünfjahresvertrag erzielt; Einigung mit dem Klub steht noch aus." },
    fr: { text: "Barcelone s'est mis d'accord sur les conditions personnelles avec Viktor Barski pour un contrat de cinq ans ; le montant reste à négocier." },
  },
  "c-011a": {
    it: { text: "Nessuna offerta è stata ricevuta per Amadou Sy. Gli intermediari stanno facendo circolare una cifra di 45 milioni di sterline per forzare le cose." },
    es: { text: "No se ha recibido ninguna oferta por Amadou Sy. Los intermediarios están inflando una cifra de 45 millones de libras para forzar el movimiento." },
    de: { text: "Für Amadou Sy ist kein Angebot eingegangen. Vermittler bringen eine Summe von 45 Mio. Pfund ins Gespräch, um Druck aufzubauen." },
    fr: { text: "Aucune offre n'a été reçue pour Amadou Sy. Les intermédiaires font circuler un montant de 45 millions de livres pour forcer le dossier." },
  },
  "c-011b": {
    it: { text: "L'offerta di 45 milioni di sterline del Newcastle per Amadou Sy è stata INVIATA: attesa una decisione nei prossimi giorni." },
    es: { text: "La oferta de 45 millones de libras del Newcastle por Amadou Sy ha sido ENVIADA: se espera una decisión en cuestión de días." },
    de: { text: "Newcastles 45-Mio.-Pfund-Angebot für Amadou Sy wurde EINGEREICHT: Eine Entscheidung wird in den nächsten Tagen erwartet." },
    fr: { text: "L'offre de 45M£ de Newcastle pour Amadou Sy a été SOUMISE : une décision est attendue dans les prochains jours." },
  },
  "c-011c": {
    it: { text: "Il Newcastle ha presentato un'offerta da 45 milioni di sterline per Amadou Sy nel tentativo di chiudere l'accordo in anticipo." },
    es: { text: "El Newcastle ha puesto sobre la mesa una oferta de 45 millones de libras por Amadou Sy para cerrar la operación cuanto antes." },
    de: { text: "Newcastle hat ein 45-Millionen-Pfund-Angebot für Amadou Sy vorgelegt, um den Transfer frühzeitig unter Dach und Fach zu bringen." },
    fr: { text: "Newcastle a formulé une offre de 45 millions de livres pour Amadou Sy afin de finaliser l'opération au plus vite." },
  },
};

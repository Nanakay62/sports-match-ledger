export type SupportedLanguage = "en" | "it" | "es" | "de" | "fr";

export const SUPPORTED_LANGUAGES: { code: SupportedLanguage; label: string }[] = [
  { code: "en", label: "EN" },
  { code: "it", label: "IT" },
  { code: "es", label: "ES" },
  { code: "de", label: "DE" },
  { code: "fr", label: "FR" },
];

export interface DictStrings {
  // Navigation & Masthead
  siteTitle: string;
  siteTagline: string;
  subHeaderAudit: string;
  navLedger: string;
  navReliability: string;
  navCorrections: string;
  navUpgrade: string;
  watchlistFree: string;
  goPro: string;
  thesisBar: string;
  storiesTracked: string;
  filterPrefix: string;

  // Filter tabs
  tabAll: string;
  tabDeveloping: string;
  tabConfirmed: string;
  tabRumours: string;
  tabDisputed: string;
  tabCorrected: string;

  // Status labels
  statusConfirmed: string;
  statusWellCorroborated: string;
  statusDeveloping: string;
  statusRumour: string;
  statusDisputed: string;
  statusCorrected: string;

  // Corrections Page
  correctionsTitle: string;
  correctionsBadge: string;
  correctionsRuleTitle: string;
  correctionsRuleText: string;
  correctionsSubheader: string;
  correctionsOrder: string;
  correctionsEmpty: string;
  originalDisputedClaim: string;
  attributedTo: string;
  correctionContext: string;
  claimSupersededNote: string;
  resolutionRecorded: string;
  viewEventDossier: string;
  originalLink: string;
  competition: string;
  claimNo: string;
  amendedAgo: string;

  // Reliability Desk
  reliabilityTitle: string;
  reliabilityBadge: string;
  reliabilityDesc: string;
  statOutlets: string;
  statBylines: string;
  statTotalClaims: string;
  statMinThreshold: string;
  tabOutlets: string;
  tabReporters: string;
  colName: string;
  colResolved: string;
  colCorrected: string;
  colScore: string;
  detailProfile: string;

  // Pro Page
  proTitle: string;
  proPromiseTitle: string;
  proPromiseText: string;
  monthly: string;
  annual: string;
  perMonth: string;
  perYear: string;
  startMonthly: string;
  startAnnual: string;

  // Rumour Lifecycle
  lifecycleTitle: string;
  lifecycleBreadcrumb: string;
  lifecycleEngine: string;
  lifecycleDesc: string;
  sourcesOnRecord: string;
  claimsOnFile: string;
  trajectoryMap: string;
  stageOrigin: string;
  stageDispute: string;
  stageCorroboration: string;
  stageResolution: string;

  // Event Dossier
  whyStatus: string;
  independentSources: string;
  firstReportedBy: string;
  leadTime: string;
  claimTimeline: string;
  relatedEvents: string;
}

export const DICTIONARY: Record<SupportedLanguage, DictStrings> = {
  en: {
    siteTitle: "Matchday Ledger",
    siteTagline: "Every claim on record.",
    subHeaderAudit: "Independent audit of the transfer market",
    navLedger: "The Ledger",
    navReliability: "Reliability desk",
    navCorrections: "Corrections",
    navUpgrade: "Upgrade",
    watchlistFree: "Watchlist 1 / 3 · Free",
    goPro: "Go Pro",
    thesisBar: "Public receipts · Append-only ledger · No unverified quotes",
    storiesTracked: "tracked stories · Live audit",
    filterPrefix: "Filter:",

    tabAll: "All entries",
    tabDeveloping: "Breaking & Developing",
    tabConfirmed: "Confirmed",
    tabRumours: "Rumours",
    tabDisputed: "Disputed",
    tabCorrected: "Corrected",

    statusConfirmed: "Confirmed",
    statusWellCorroborated: "Well corroborated",
    statusDeveloping: "Developing",
    statusRumour: "Rumour",
    statusDisputed: "Disputed",
    statusCorrected: "Corrected",

    correctionsTitle: "Corrections & Retractions",
    correctionsBadge: "Accountability Ledger · Policy §12",
    correctionsRuleTitle: "Strict Append-Only Rule:",
    correctionsRuleText:
      "Stories on this platform are never quietly updated or scrubbed. When an outlet issues a retraction, when reported figures collapse, or when official club filings dispute a claim, the record is preserved alongside the outcome.",
    correctionsSubheader: "recorded corrections & disputes",
    correctionsOrder: "Newest resolutions first",
    correctionsEmpty: "No active corrections on record today.",
    originalDisputedClaim: "Original Disputed Claim",
    attributedTo: "Attributed to:",
    correctionContext: "Correction / Resolution Context",
    claimSupersededNote: "Claim superseded following conflicting evidence or official club denial.",
    resolutionRecorded: "Resolution recorded:",
    viewEventDossier: "View full event dossier →",
    originalLink: "Original link",
    competition: "Competition:",
    claimNo: "Claim №",
    amendedAgo: "Amended",

    reliabilityTitle: "The Reliability Desk",
    reliabilityBadge: "Public receipts · Wilson score",
    reliabilityDesc:
      "Every substantive report is recorded at ingestion with its author, outlet, and timestamp. When an official outcome settles, claims are resolved and rolled up into a public reliability record.",
    statOutlets: "Tracked Outlets",
    statBylines: "Tracked Bylines",
    statTotalClaims: "Total Claims",
    statMinThreshold: "10 resolved",
    tabOutlets: "Outlets & Newsrooms",
    tabReporters: "Reporters & Bylines",
    colName: "Name",
    colResolved: "Resolved claims",
    colCorrected: "Corrected",
    colScore: "Reliability score",
    detailProfile: "View reliability ledger →",

    proTitle: "The record is free. The archive is Pro.",
    proPromiseTitle: "Our promise:",
    proPromiseText:
      "the current status of every tracked claim (Confirmed to Corrected) is free, and always will be. Pro never touches the answer to “what's the latest?”. It only deepens the record behind it.",
    monthly: "Monthly",
    annual: "Annual",
    perMonth: "/ month",
    perYear: "/ year",
    startMonthly: "Start monthly: £6/mo",
    startAnnual: "Start annual: £45/yr",

    lifecycleTitle: "Rumour Lifecycle Trajectory",
    lifecycleBreadcrumb: "Rumour Lifecycle Trajectory",
    lifecycleEngine: "Rumour Audit & Corroboration Engine",
    lifecycleDesc:
      "Complete chronological lifecycle trace: tracking this story from the initial unsourced leak through multi-language wire syndications, corroboration, and eventual verified outcome.",
    sourcesOnRecord: "independent source roots",
    claimsOnFile: "total claims on file",
    trajectoryMap: "Chronological Trajectory Map",
    stageOrigin: "First Reported",
    stageDispute: "Contradiction / Dispute",
    stageCorroboration: "Corroboration",
    stageResolution: "Official Resolution",

    whyStatus: "Why this status",
    independentSources: "Independent sources",
    firstReportedBy: "First reported by",
    leadTime: "lead time",
    claimTimeline: "Claim timeline & provenance",
    relatedEvents: "Related transfer dossiers",
  },
  it: {
    siteTitle: "Matchday Ledger",
    siteTagline: "Tutte le affermazioni registrate.",
    subHeaderAudit: "Revisione indipendente del calciomercato",
    navLedger: "Il Registro",
    navReliability: "Banco affidabilità",
    navCorrections: "Rettifiche",
    navUpgrade: "Aggiorna",
    watchlistFree: "Watchlist 1 / 3 · Gratuito",
    goPro: "Passa a Pro",
    thesisBar: "Ricevute pubbliche · Registro append-only · Nessuna citazione non verificata",
    storiesTracked: "notizie tracciate · Audit in tempo reale",
    filterPrefix: "Filtro:",

    tabAll: "Tutte le voci",
    tabDeveloping: "In sviluppo",
    tabConfirmed: "Confermato",
    tabRumours: "Indiscrezioni",
    tabDisputed: "Contestato",
    tabCorrected: "Rettificato",

    statusConfirmed: "Confermato",
    statusWellCorroborated: "Ben confermato",
    statusDeveloping: "In sviluppo",
    statusRumour: "Indiscrezione",
    statusDisputed: "Contestato",
    statusCorrected: "Rettificato",

    correctionsTitle: "Rettifiche e Smentite",
    correctionsBadge: "Registro di Responsabilità · Norma §12",
    correctionsRuleTitle: "Regola Ferrea Append-Only:",
    correctionsRuleText:
      "Le notizie su questa piattaforma non vengono mai modificate o cancellate in silenzio. Quando una testata emette una smentita o quando documenti ufficiali smentiscono una notizia, il verbale originale rimane archiviato insieme all'esito.",
    correctionsSubheader: "rettifiche e contestazioni registrate",
    correctionsOrder: "Risoluzioni più recenti per prime",
    correctionsEmpty: "Nessuna rettifica attiva registrata oggi.",
    originalDisputedClaim: "Affermazione Contestata Originale",
    attributedTo: "Attribuito a:",
    correctionContext: "Contesto di Rettifica / Risoluzione",
    claimSupersededNote: "Affermazione sostituita a seguito di prove contrastanti o smentita ufficiale del club.",
    resolutionRecorded: "Risoluzione registrata:",
    viewEventDossier: "Vedi fascicolo completo →",
    originalLink: "Link originale",
    competition: "Competizione:",
    claimNo: "Reclamo №",
    amendedAgo: "Modificato",

    reliabilityTitle: "Il Banco di Affidabilità",
    reliabilityBadge: "Ricevute pubbliche · Punteggio Wilson",
    reliabilityDesc:
      "Ogni articolo sostanziale viene registrato al momento dell'ingestione con autore, testata e data. Quando l'esito ufficiale si chiude, le affermazioni vengono risolte ed elaborate in un indice pubblico di affidabilità.",
    statOutlets: "Testate Tracciate",
    statBylines: "Firme Tracciate",
    statTotalClaims: "Affermazioni Totali",
    statMinThreshold: "10 risolte",
    tabOutlets: "Testate e Redazioni",
    tabReporters: "Giornalisti e Firme",
    colName: "Nome",
    colResolved: "Affermazioni risolte",
    colCorrected: "Rettificate",
    colScore: "Punteggio di affidabilità",
    detailProfile: "Vedi registro affidabilità →",

    proTitle: "Il verbale è gratuito. L'archivio è Pro.",
    proPromiseTitle: "La nostra promessa:",
    proPromiseText:
      "Lo stato attuale di ogni affermazione tracciata è gratuito e lo sarà sempre. Pro offre profondità d'archivio, esportazioni, avvisi ed elenchi illimitati.",
    monthly: "Mensile",
    annual: "Annuale",
    perMonth: "/ mese",
    perYear: "/ anno",
    startMonthly: "Inizia mensile: £6/mese",
    startAnnual: "Inizia annuale: £45/anno",

    lifecycleTitle: "Traiettoria del Ciclo di Vita",
    lifecycleBreadcrumb: "Traiettoria del Ciclo di Vita",
    lifecycleEngine: "Motore di Corroborazione e Audit Voci",
    lifecycleDesc:
      "Tracciamento cronologico completo: segue la voce dalla fuga iniziale non verificata fino alle conferme multi-lingua e all'esito ufficiale accertato.",
    sourcesOnRecord: "radici di fonti indipendenti",
    claimsOnFile: "affermazioni totali agli atti",
    trajectoryMap: "Mappa Cronologica della Traiettoria",
    stageOrigin: "Prima Notizia",
    stageDispute: "Contraddizione / Smentita",
    stageCorroboration: "Corroborazione",
    stageResolution: "Risoluzione Ufficiale",

    whyStatus: "Perché questo stato",
    independentSources: "Fonti indipendenti",
    firstReportedBy: "Segnalato per primo da",
    leadTime: "tempo di anticipo",
    claimTimeline: "Cronologia e provenienza affermazioni",
    relatedEvents: "Dossier di mercato correlati",
  },
  es: {
    siteTitle: "Matchday Ledger",
    siteTagline: "Cada afirmación registrada.",
    subHeaderAudit: "Auditoría independiente del mercado de fichajes",
    navLedger: "El Registro",
    navReliability: "Mesa de fiabilidad",
    navCorrections: "Correcciones",
    navUpgrade: "Mejorar",
    watchlistFree: "Seguimiento 1 / 3 · Gratis",
    goPro: "Hazte Pro",
    thesisBar: "Recibos públicos · Registro inmutable · Cero citas inventadas",
    storiesTracked: "historias seguidas · Auditoría en vivo",
    filterPrefix: "Filtro:",

    tabAll: "Todas las entradas",
    tabDeveloping: "En desarrollo",
    tabConfirmed: "Confirmado",
    tabRumours: "Rumores",
    tabDisputed: "Disputado",
    tabCorrected: "Corregido",

    statusConfirmed: "Confirmado",
    statusWellCorroborated: "Bien corroborado",
    statusDeveloping: "En desarrollo",
    statusRumour: "Rumor",
    statusDisputed: "Disputado",
    statusCorrected: "Corregido",

    correctionsTitle: "Correcciones y Retractaciones",
    correctionsBadge: "Registro de Responsabilidad · Cláusula §12",
    correctionsRuleTitle: "Regla Estricta Solo-Añadir:",
    correctionsRuleText:
      "Las noticias en esta plataforma nunca se actualizan ni borran en silencio. Cuando un medio emite una retractación o los clubes desmienten una cifra, el registro original se conserva junto con el desenlace.",
    correctionsSubheader: "correcciones y disputas archivadas",
    correctionsOrder: "Resoluciones más recientes primero",
    correctionsEmpty: "No hay correcciones activas hoy.",
    originalDisputedClaim: "Afirmación Disputada Original",
    attributedTo: "Atribuido a:",
    correctionContext: "Contexto de Corrección / Resolución",
    claimSupersededNote: "Afirmación sustituida tras pruebas contradictorias o desmentido oficial del club.",
    resolutionRecorded: "Resolución registrada:",
    viewEventDossier: "Ver expediente completo →",
    originalLink: "Enlace original",
    competition: "Competición:",
    claimNo: "Afirmación №",
    amendedAgo: "Modificado hace",

    reliabilityTitle: "La Mesa de Fiabilidad",
    reliabilityBadge: "Recibos públicos · Puntuación Wilson",
    reliabilityDesc:
      "Cada información relevante se registra al ser captada con su autor, medio y hora. Cuando se produce un desenlace oficial, las afirmaciones se contrastan y se reflejan en un índice público de fiabilidad.",
    statOutlets: "Medios Auditados",
    statBylines: "Firmas Auditadas",
    statTotalClaims: "Afirmaciones Totales",
    statMinThreshold: "10 resueltas",
    tabOutlets: "Medios y Redacciones",
    tabReporters: "Periodistas y Firmas",
    colName: "Nombre",
    colResolved: "Afirmaciones resueltas",
    colCorrected: "Corregidas",
    colScore: "Puntuación de fiabilidad",
    detailProfile: "Ver registro de fiabilidad →",

    proTitle: "El registro es gratis. El archivo es Pro.",
    proPromiseTitle: "Nuestra promesa:",
    proPromiseText:
      "El estado actual de cada rumor siempre será gratis. Pro profundiza el archivo histórico, exportaciones, alertas y listas de seguimiento ilimitadas.",
    monthly: "Mensual",
    annual: "Anual",
    perMonth: "/ mes",
    perYear: "/ año",
    startMonthly: "Comenzar mensual: £6/mes",
    startAnnual: "Comenzar anual: £45/año",

    lifecycleTitle: "Trayectoria del Ciclo del Rumor",
    lifecycleBreadcrumb: "Trayectoria del Ciclo del Rumor",
    lifecycleEngine: "Motor de Auditoría y Corroboración de Rumores",
    lifecycleDesc:
      "Trazabilidad cronológica completa: desde la filtración inicial sin confirmar hasta las coberturas internacionales y la confirmación oficial final.",
    sourcesOnRecord: "fuentes raíz independientes",
    claimsOnFile: "afirmaciones en el expediente",
    trajectoryMap: "Mapa Cronológico de Trayectoria",
    stageOrigin: "Primera Publicación",
    stageDispute: "Contradicción / Desmentido",
    stageCorroboration: "Corroboración",
    stageResolution: "Resolución Oficial",

    whyStatus: "Por qué este estado",
    independentSources: "Fuentes independientes",
    firstReportedBy: "Publicado primero por",
    leadTime: "tiempo de adelanto",
    claimTimeline: "Línea de tiempo y procedencia de afirmaciones",
    relatedEvents: "Expedientes de fichajes relacionados",
  },
  de: {
    siteTitle: "Matchday Ledger",
    siteTagline: "Jede Behauptung im Protokoll.",
    subHeaderAudit: "Unabhängige Prüfung des Transfermarktes",
    navLedger: "Das Hauptbuch",
    navReliability: "Zuverlässigkeit",
    navCorrections: "Korrekturen",
    navUpgrade: "Upgrade",
    watchlistFree: "Watchlist 1 / 3 · Kostenlos",
    goPro: "Zu Pro wechseln",
    thesisBar: "Öffentliche Nachweise · Unveränderliches Protokoll · Keine unbestätigten Zitate",
    storiesTracked: "verfolgte Meldungen · Live-Prüfung",
    filterPrefix: "Filter:",

    tabAll: "Alle Einträge",
    tabDeveloping: "In Entwicklung",
    tabConfirmed: "Bestätigt",
    tabRumours: "Gerüchte",
    tabDisputed: "Bestritten",
    tabCorrected: "Korrigiert",

    statusConfirmed: "Bestätigt",
    statusWellCorroborated: "Gut belegt",
    statusDeveloping: "In Entwicklung",
    statusRumour: "Gerücht",
    statusDisputed: "Bestritten",
    statusCorrected: "Korrigiert",

    correctionsTitle: "Korrekturen & Widerrufe",
    correctionsBadge: "Rechenschaftsregister · Richtlinie §12",
    correctionsRuleTitle: "Strikte Protokoll-Regel:",
    correctionsRuleText:
      "Berichte auf dieser Plattform werden niemals stillschweigend geändert oder gelöscht. Wenn Medien einen Widerruf veröffentlichen oder offizielle Vereinsmitteilungen einer Meldung widersprechen, bleibt das Protokoll erhalten.",
    correctionsSubheader: "erfasste Korrekturen & Widersprüche",
    correctionsOrder: "Neueste Entscheidungen zuerst",
    correctionsEmpty: "Heute keine aktiven Korrekturen verzeichnet.",
    originalDisputedClaim: "Ursprünglich bestrittene Behauptung",
    attributedTo: "Zugeschrieben an:",
    correctionContext: "Korrektur- / Entscheidungskontext",
    claimSupersededNote: "Aussage nach widersprüchlichen Beweisen oder Vereinsdementi korrigiert.",
    resolutionRecorded: "Entscheidung erfasst:",
    viewEventDossier: "Vollständiges Dossier ansehen →",
    originalLink: "Original-Link",
    competition: "Wettbewerb:",
    claimNo: "Aussage №",
    amendedAgo: "Geändert vor",

    reliabilityTitle: "Das Zuverlässigkeits-Desk",
    reliabilityBadge: "Öffentliche Nachweise · Wilson-Score",
    reliabilityDesc:
      "Jeder substanzielle Bericht wird bei Erfassung mit Autor, Medium und Zeitstempel registriert. Sobald das offizielle Ergebnis feststeht, werden Behauptungen bewertet und in ein öffentliches Zuverlässigkeitsprofil überführt.",
    statOutlets: "Erfasste Medien",
    statBylines: "Erfasste Autoren",
    statTotalClaims: "Gesamtaussagen",
    statMinThreshold: "10 bewertet",
    tabOutlets: "Medien & Redaktionen",
    tabReporters: "Journalisten & Autoren",
    colName: "Name",
    colResolved: "Bewertete Aussagen",
    colCorrected: "Korrigiert",
    colScore: "Zuverlässigkeitswert",
    detailProfile: "Zuverlässigkeitsbuch ansehen →",

    proTitle: "Das Protokoll ist frei. Das Archiv ist Pro.",
    proPromiseTitle: "Unser Versprechen:",
    proPromiseText:
      "Der aktuelle Status jeder erfassten Meldung ist und bleibt kostenlos. Pro vertieft den Zugriff auf das Gesamtarchiv, Exporte, Echtzeit-Benachrichtigungen und unbegrenzte Watchlists.",
    monthly: "Monatlich",
    annual: "Jährlich",
    perMonth: "/ Monat",
    perYear: "/ Jahr",
    startMonthly: "Monatlich starten: £6/Monat",
    startAnnual: "Jährlich starten: £45/Jahr",

    lifecycleTitle: "Gerüchte-Lebenszyklus",
    lifecycleBreadcrumb: "Gerüchte-Lebenszyklus",
    lifecycleEngine: "Gerüchte-Audit & Bestätigungs-Engine",
    lifecycleDesc:
      "Vollständige chronologische Ablaufverfolgung: von der ersten unbestätigten Meldung über internationale Agenturberichte bis hin zur offiziellen Bestätigung.",
    sourcesOnRecord: "unabhängige Primärquellen",
    claimsOnFile: "registrierte Behauptungen",
    trajectoryMap: "Chronologische Ablaufkarte",
    stageOrigin: "Erstbericht",
    stageDispute: "Widerspruch / Dementi",
    stageCorroboration: "Bestätigung",
    stageResolution: "Offizielle Entscheidung",

    whyStatus: "Warum dieser Status",
    independentSources: "Unabhängige Quellen",
    firstReportedBy: "Zuerst berichtet von",
    leadTime: "Vorsprung",
    claimTimeline: "Chronologie & Herkunft der Aussagen",
    relatedEvents: "Verwandte Transferdossiers",
  },
  fr: {
    siteTitle: "Matchday Ledger",
    siteTagline: "Chaque allégation au registre.",
    subHeaderAudit: "Audit indépendant du marché des transferts",
    navLedger: "Le Registre",
    navReliability: "Bureau de fiabilité",
    navCorrections: "Rectifications",
    navUpgrade: "S'abonner",
    watchlistFree: "Suivi 1 / 3 · Gratuit",
    goPro: "Passer à Pro",
    thesisBar: "Preuves publiques · Registre immuable · Zéro citation non vérifiée",
    storiesTracked: "dossiers suivis · Audit en direct",
    filterPrefix: "Filtre :",

    tabAll: "Toutes les entrées",
    tabDeveloping: "En cours",
    tabConfirmed: "Confirmé",
    tabRumours: "Rumeurs",
    tabDisputed: "Contesté",
    tabCorrected: "Rectifié",

    statusConfirmed: "Confirmé",
    statusWellCorroborated: "Bien corroboré",
    statusDeveloping: "En cours",
    statusRumour: "Rumeur",
    statusDisputed: "Contesté",
    statusCorrected: "Rectifié",

    correctionsTitle: "Rectifications & Rétractations",
    correctionsBadge: "Registre de Responsabilité · Règle §12",
    correctionsRuleTitle: "Règle Stricte Append-Only :",
    correctionsRuleText:
      "Les articles sur cette plateforme ne sont jamais modifiés ou supprimés discrètement. Lorsqu'un média publie une rétractation ou qu'un club dément une information, l'enregistrement initial est conservé avec l'issue.",
    correctionsSubheader: "rectifications et litiges enregistrés",
    correctionsOrder: "Résolutions récentes en premier",
    correctionsEmpty: "Aucune rectification active aujourd'hui.",
    originalDisputedClaim: "Allégation Contestée Initiale",
    attributedTo: "Attribué à :",
    correctionContext: "Contexte de Rectification / Résolution",
    claimSupersededNote: "Allégation remplacée à la suite de preuves contradictoires ou d'un démenti officiel du club.",
    resolutionRecorded: "Résolution enregistrée :",
    viewEventDossier: "Voir le dossier complet →",
    originalLink: "Lien original",
    competition: "Compétition :",
    claimNo: "Allégation №",
    amendedAgo: "Modifié il y a",

    reliabilityTitle: "Le Bureau de Fiabilité",
    reliabilityBadge: "Preuves publiques · Score de Wilson",
    reliabilityDesc:
      "Chaque information importante est enregistrée dès sa collecte avec son auteur, son média et son horodatage. Quand un résultat officiel est scellé, les allégations sont évaluées dans un registre public de fiabilité.",
    statOutlets: "Médias Audités",
    statBylines: "Signatures Auditées",
    statTotalClaims: "Allégations Totales",
    statMinThreshold: "10 résolues",
    tabOutlets: "Médias & Rédactions",
    tabReporters: "Journalistes & Signatures",
    colName: "Nom",
    colResolved: "Allégations résolues",
    colCorrected: "Rectifiées",
    colScore: "Score de fiabilité",
    detailProfile: "Consulter le registre →",

    proTitle: "Le registre est libre. L'archive est Pro.",
    proPromiseTitle: "Notre engagement :",
    proPromiseText:
      "Le statut de chaque allégation est et restera toujours gratuit. Pro permet d'accéder à l'archive complète, aux exports, aux alertes et aux listes de suivi illimitées.",
    monthly: "Mensuel",
    annual: "Annuel",
    perMonth: "/ mois",
    perYear: "/ an",
    startMonthly: "Démarrer au mois : £6/mois",
    startAnnual: "Démarrer à l'année : £45/an",

    lifecycleTitle: "Trajectoire du Cycle de Vie",
    lifecycleBreadcrumb: "Trajectoire du Cycle de Vie",
    lifecycleEngine: "Moteur d'Audit et de Corroboration des Rumeurs",
    lifecycleDesc:
      "Traçabilité chronologique complète : suivi de la rumeur depuis la fuite initiale jusqu'aux dépêches internationales et à l'officialisation définitive.",
    sourcesOnRecord: "sources indépendantes racines",
    claimsOnFile: "allégations au dossier",
    trajectoryMap: "Carte Chronologique de la Trajectoire",
    stageOrigin: "Première Publication",
    stageDispute: "Contradiction / Démenti",
    stageCorroboration: "Corroboration",
    stageResolution: "Résolution Officielle",

    whyStatus: "Pourquoi ce statut",
    independentSources: "Sources indépendantes",
    firstReportedBy: "Rapporté d'abord par",
    leadTime: "d'avance",
    claimTimeline: "Chronologie & provenance des allégations",
    relatedEvents: "Dossiers transferts associés",
  },
};

export function getDictionary(lang?: string): DictStrings {
  const norm = (lang || "en").toLowerCase() as SupportedLanguage;
  return DICTIONARY[norm] || DICTIONARY.en;
}

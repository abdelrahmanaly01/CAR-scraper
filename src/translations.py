"""Desktop UI strings. The public CAR website keeps its own Portuguese UI."""
LANGUAGES = {"en": "English", "pt-BR": "Português (Brasil)"}

TEXT = {
    "en": {
        "checking_start": "Checking coordinates and property boundaries...",
        "checking_candidates": "Checking potential properties ({current}/{total})...",
        "candidate_notice": "Select a property. Repeated searches may not find every property.",
        "partial_results": "Some searches failed. Results may be incomplete; retry if needed.",
        "choose_candidate": "Choose a property to view its details",
        "inside": "Point inside boundary", "outside": "Point outside boundary", "unknown_boundary": "Boundary could not be checked",
        "boundary_distance": "Distance to boundary",
        "download_zip": "Download ZIP",
        "downloading": "Downloading and checking ZIP...",
        "download_saved": "ZIP verified and saved successfully.",
        "download_failed": "Download failed. No completed file was saved.",
        "download_wait": "Please wait for the download to finish before closing the application.",
        "statement": "Open statement in Chrome",
        "statement_error": "Could not open the statement in Chrome.",
        "window": "CAR | Property Finder", "brand": "CAR / PUBLIC MAP",
        "title": "Find your property", "intro": "Enter coordinates to open the property details.",
        "latitude": "Latitude", "longitude": "Longitude", "south": "South is negative",
        "west": "West is negative", "sample": "Use sample coordinates", "find": "Find property",
        "cancel": "Cancel", "end": "End session", "idle": "Ready when you are",
        "browser": "Start browser", "website": "Open website", "map": "Load search form",
        "coordinates": "Resolve coordinates", "property": "Search CAR number", "details": "Open details",
        "progress_browser": "Starting your browser session...",
        "progress_website": "Opening the public CAR website...",
        "progress_map": "Loading the registration search form...",
        "progress_coordinates": "Looking up your coordinates in the CAR service...",
        "progress_property": "Searching the website by the returned CAR number...",
        "progress_details": "Opening and checking the property details...",
        "ready": "Property ready — continue in the browser",
        "cancelled": "Session cancelled. Ready for another search.",
        "closing": "Closing this session...", "failed": "We could not open this property.",
        "retry": "Check the coordinates and your connection, then try again.",
        "mismatch": "The website displayed a different CAR registration. The session was stopped to avoid opening the wrong property.",
        "failed_title": "Property search failed", "unexpected": "The browser session ended unexpectedly.",
        "finished_title": "Session finished", "another": "The browser is closed.\n\nWould you like to find another property?",
        "again": "Ready for another property", "yes": "Yes, new session", "no": "No, exit", "ok": "OK",
        "technical": "Technical details", "invalid": "Invalid coordinates. Use decimal degrees or DMS; latitude: -90 to 90, longitude: -180 to 180.",
        "no_property": "No registered property was found at these coordinates.",
        "timeout": "The portal did not respond in time. Check your connection and try again.",
        "browser_missing": "The browser is not installed. Run setup.bat, then try again.",
        "preference_error": "Language changed, but the preference could not be saved.",
    },
    "pt-BR": {
        "checking_start": "Verificando coordenadas e limites dos imóveis...",
        "checking_candidates": "Verificando possíveis imóveis ({current}/{total})...",
        "candidate_notice": "Selecione um imóvel. A busca pode não encontrar todos os imóveis.",
        "partial_results": "Algumas consultas falharam. Os resultados podem estar incompletos.",
        "choose_candidate": "Escolha um imóvel para ver os detalhes",
        "inside": "Ponto dentro do limite", "outside": "Ponto fora do limite", "unknown_boundary": "Não foi possível verificar o limite",
        "boundary_distance": "Distância até o limite",
        "download_zip": "Baixar ZIP",
        "downloading": "Baixando e verificando ZIP...",
        "download_saved": "ZIP verificado e salvo com sucesso.",
        "download_failed": "Falha no download. Nenhum arquivo completo foi salvo.",
        "download_wait": "Aguarde o término do download antes de fechar o aplicativo.",
        "statement": "Demonstrativo no Chrome",
        "statement_error": "Não foi possível abrir o demonstrativo no Chrome.",
        "window": "CAR | Consulta de imóveis", "brand": "CAR / CONSULTA PÚBLICA",
        "title": "Encontre seu imóvel", "intro": "Informe as coordenadas para abrir os detalhes do imóvel.",
        "latitude": "Latitude", "longitude": "Longitude", "south": "Sul: valor negativo",
        "west": "Oeste: valor negativo", "sample": "Usar coordenadas de exemplo", "find": "Buscar imóvel",
        "cancel": "Cancelar", "end": "Encerrar sessão", "idle": "Pronto para começar",
        "browser": "Iniciar navegador", "website": "Abrir site", "map": "Carregar busca",
        "coordinates": "Consultar coordenadas", "property": "Buscar número CAR", "details": "Abrir detalhes",
        "progress_browser": "Iniciando a sessão do navegador...",
        "progress_website": "Abrindo o site de consulta pública do CAR...",
        "progress_map": "Carregando o formulário de busca por registro...",
        "progress_coordinates": "Consultando suas coordenadas no serviço do CAR...",
        "progress_property": "Buscando no site o número CAR retornado...",
        "progress_details": "Abrindo e conferindo os detalhes do imóvel...",
        "ready": "Imóvel pronto — continue no navegador",
        "cancelled": "Sessão cancelada. Pronto para outra busca.",
        "closing": "Encerrando esta sessão...", "failed": "Não foi possível abrir este imóvel.",
        "retry": "Confira as coordenadas e sua conexão e tente novamente.",
        "mismatch": "O site exibiu outro registro CAR. A sessão foi interrompida para evitar a abertura do imóvel errado.",
        "failed_title": "Falha na busca do imóvel", "unexpected": "A sessão do navegador foi encerrada inesperadamente.",
        "finished_title": "Sessão encerrada", "another": "O navegador foi fechado.\n\nDeseja buscar outro imóvel?",
        "again": "Pronto para buscar outro imóvel", "yes": "Sim, nova sessão", "no": "Não, sair", "ok": "OK",
        "technical": "Detalhes técnicos", "invalid": "Coordenadas inválidas. Use graus decimais ou DMS; latitude: -90 a 90, longitude: -180 a 180.",
        "no_property": "Nenhum imóvel cadastrado foi encontrado nessas coordenadas.",
        "timeout": "O portal não respondeu a tempo. Confira sua conexão e tente novamente.",
        "browser_missing": "O navegador não está instalado. Execute setup.bat e tente novamente.",
        "preference_error": "O idioma foi alterado, mas não foi possível salvar a preferência.",
    },
}


def error_key(message: str) -> str:
    lowered = message.lower()
    if "property mismatch" in lowered:
        return "mismatch"
    if "no car property" in lowered or "no property details button" in lowered:
        return "no_property"
    if "timeout" in lowered or "in time" in lowered:
        return "timeout"
    if "executable doesn't exist" in lowered or "playwright install" in lowered:
        return "browser_missing"
    return "retry"

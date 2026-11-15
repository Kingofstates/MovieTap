/**
 * MovieTap Web - Client-side Application (v3.0)
 * Features:
 * - AnimeWorld-inspired Centered Hero with Wallpaper Crossfade Loop (hero_1.jpg to hero_10.jpg)
 * - Multi-Engine Search (MovieBox, Dramachi, 4KHDHub, All) with Rich Poster Suggestions
 * - Telugu Priority for Default Audio Language
 * - Hotstar/Disney+ Dual-Column Audio & Subtitles In-Player Drawer
 * - Fixed Subtitle Overlay (no duplicate cues)
 * - Browser Video & Subtitle Downloader (Details Page & In-Player)
 * - Smooth scroll navigation to Movies/Series catalog
 * - Watch History & Watchlist persistence
 */

// Wallpapers list (watermark-free 10-image collection)
const WALLPAPERS = [
  '/static/wallpapers/hero_1.jpg',
  '/static/wallpapers/hero_2.jpg',
  '/static/wallpapers/hero_3.jpg',
  '/static/wallpapers/hero_4.jpg',
  '/static/wallpapers/hero_5.jpg',
  '/static/wallpapers/hero_6.jpg',
  '/static/wallpapers/hero_7.jpg',
  '/static/wallpapers/hero_8.jpg',
  '/static/wallpapers/hero_9.jpg',
  '/static/wallpapers/hero_10.jpg'
];

// Global State
const state = {
  activeTab: 'home',
  activeFilter: 'all',
  activeProvider: 'all',
  catalogItems: [],
  currentDetails: null,
  activeDub: null,
  selectedSeason: 1,
  selectedEpisode: 1,
  currentStreams: [],
  activeStream: null,
  currentCaptions: [],
  activeCaption: null,
  watchHistory: JSON.parse(localStorage.getItem('movietap_history') || localStorage.getItem('moviebox_history') || '[]'),
  watchlist: JSON.parse(localStorage.getItem('movietap_watchlist') || localStorage.getItem('moviebox_watchlist') || '[]'),
  searchTimeout: null,
  controlsTimeout: null,
  wallpaperIndex: 0,
  wallpaperInterval: null,
  isPlaying: false,

  // Download Dialog State
  downloadDub: null,
  downloadStream: null,
  downloadCaption: null
};

// DOM Mapping
const DOM = {
  // Navigation & Branding
  brandLogo: document.getElementById('brandLogo'),
  navLinks: document.querySelectorAll('.nav-links .nav-link'),
  heroNavButtons: document.querySelectorAll('.hero-pill-btn'),
  watchlistCount: document.getElementById('watchlistCount'),
  heroWatchlistCount: document.getElementById('heroWatchlistCount'),
  btnQuickSearch: document.getElementById('btnQuickSearch'),

  // Views & Sections
  homeView: document.getElementById('homeView'),
  searchResultsView: document.getElementById('searchResultsView'),
  watchlistView: document.getElementById('watchlistView'),
  catalogSection: document.getElementById('catalogSection'),
  catalogHeaderTitle: document.getElementById('catalogHeaderTitle'),
  searchHeaderTitle: document.getElementById('searchHeaderTitle'),
  backToHomeBtn: document.getElementById('backToHomeBtn'),

  // Grids
  trendingGrid: document.getElementById('trendingGrid'),
  searchGrid: document.getElementById('searchGrid'),
  watchlistGrid: document.getElementById('watchlistGrid'),
  continueWatchingSection: document.getElementById('continueWatchingSection'),
  continueWatchingGrid: document.getElementById('continueWatchingGrid'),
  clearHistoryBtn: document.getElementById('clearHistoryBtn'),
  clearWatchlistBtn: document.getElementById('clearWatchlistBtn'),

  // Wallpapers
  wallpaperLoopBg: document.getElementById('wallpaperLoopBg'),
  wallpaperBottomBg: document.getElementById('wallpaperBottomBg'),

  // Search
  searchInput: document.getElementById('searchInput'),
  searchClear: document.getElementById('searchClear'),
  searchSubmitBtn: document.getElementById('searchSubmitBtn'),
  suggestionsDropdown: document.getElementById('suggestionsDropdown'),
  quickGenreTags: document.getElementById('quickGenreTags'),

  // Details Modal
  detailsModal: document.getElementById('detailsModal'),
  modalBackdrop: document.getElementById('modalBackdrop'),
  modalCloseBtn: document.getElementById('modalCloseBtn'),
  modalHeroBg: document.getElementById('modalHeroBg'),
  modalPoster: document.getElementById('modalPoster'),
  modalTitle: document.getElementById('modalTitle'),
  modalType: document.getElementById('modalType'),
  modalProvider: document.getElementById('modalProvider'),
  modalRating: document.getElementById('modalRating'),
  modalYear: document.getElementById('modalYear'),
  modalDuration: document.getElementById('modalDuration'),
  modalGenres: document.getElementById('modalGenres'),
  modalDescription: document.getElementById('modalDescription'),
  modalDirectorRow: document.getElementById('modalDirectorRow'),
  modalDirector: document.getElementById('modalDirector'),
  modalStarsRow: document.getElementById('modalStarsRow'),
  modalStars: document.getElementById('modalStars'),
  modalPlayBtn: document.getElementById('modalPlayBtn'),
  modalDownloadBtn: document.getElementById('modalDownloadBtn'),
  modalWatchlistBtn: document.getElementById('modalWatchlistBtn'),

  // Audio Languages in Modal
  modalAudioSection: document.getElementById('modalAudioSection'),
  modalAudioChipsGrid: document.getElementById('modalAudioChipsGrid'),
  audioLanguagesCount: document.getElementById('audioLanguagesCount'),

  // TV Series Section
  modalSeriesSection: document.getElementById('modalSeriesSection'),
  seasonSelect: document.getElementById('seasonSelect'),
  episodeGrid: document.getElementById('episodeGrid'),

  // Stream & Subtitles Previews
  streamQualitiesList: document.getElementById('streamQualitiesList'),
  qualitiesCount: document.getElementById('qualitiesCount'),
  modalSubtitlesList: document.getElementById('modalSubtitlesList'),
  subtitlesCount: document.getElementById('subtitlesCount'),

  // Download Modal
  downloadModal: document.getElementById('downloadModal'),
  downloadModalBackdrop: document.getElementById('downloadModalBackdrop'),
  downloadModalCloseBtn: document.getElementById('downloadModalCloseBtn'),
  downloadMediaTitle: document.getElementById('downloadMediaTitle'),
  downloadMediaSubtitle: document.getElementById('downloadMediaSubtitle'),
  downloadLangChips: document.getElementById('downloadLangChips'),
  downloadQualityChips: document.getElementById('downloadQualityChips'),
  downloadSubtitleChips: document.getElementById('downloadSubtitleChips'),
  btnCancelDownload: document.getElementById('btnCancelDownload'),
  btnConfirmDownload: document.getElementById('btnConfirmDownload'),

  // Video Player
  playerModal: document.getElementById('playerModal'),
  playerContainer: document.getElementById('playerContainer'),
  videoElement: document.getElementById('videoElement'),
  subtitleOverlay: document.getElementById('subtitleOverlay'),
  playerCloseBtn: document.getElementById('playerCloseBtn'),
  playerMediaTitle: document.getElementById('playerMediaTitle'),
  playerMediaSubtitle: document.getElementById('playerMediaSubtitle'),
  playerAudioBadge: document.getElementById('playerAudioBadge'),
  playerQualityBadge: document.getElementById('playerQualityBadge'),
  playerCenterOverlay: document.getElementById('playerCenterOverlay'),
  playerBigPlayBtn: document.getElementById('playerBigPlayBtn'),
  playerSpinner: document.getElementById('playerSpinner'),
  playerControlsBar: document.getElementById('playerControlsBar'),

  // Hotstar Audio & Subtitles Drawer
  audioSubDrawer: document.getElementById('audioSubDrawer'),
  drawerCloseBtn: document.getElementById('drawerCloseBtn'),
  btnAudioSubtitles: document.getElementById('btnAudioSubtitles'),
  drawerAudioList: document.getElementById('drawerAudioList'),
  drawerSubtitlesList: document.getElementById('drawerSubtitlesList'),

  // Player Controls
  progressContainer: document.getElementById('progressContainer'),
  progressTrack: document.querySelector('.player-progress-track'),
  progressBuffered: document.getElementById('progressBuffered'),
  progressFilled: document.getElementById('progressFilled'),
  progressHoverTime: document.getElementById('progressHoverTime'),
  btnPlayPause: document.getElementById('btnPlayPause'),
  btnRewind: document.getElementById('btnRewind'),
  btnForward: document.getElementById('btnForward'),
  btnVolume: document.getElementById('btnVolume'),
  volumeSlider: document.getElementById('volumeSlider'),
  currentTime: document.getElementById('currentTime'),
  totalDuration: document.getElementById('totalDuration'),
  btnNextEpisode: document.getElementById('btnNextEpisode'),
  btnQuality: document.getElementById('btnQuality'),
  qualityBadgeLabel: document.getElementById('qualityBadgeLabel'),
  qualityMenu: document.getElementById('qualityMenu'),
  qualityOptionsList: document.getElementById('qualityOptionsList'),
  btnSpeed: document.getElementById('btnSpeed'),
  speedLabel: document.getElementById('speedLabel'),
  speedMenu: document.getElementById('speedMenu'),
  btnPlayerDownload: document.getElementById('btnPlayerDownload'),
  btnPiP: document.getElementById('btnPiP'),
  btnFullscreen: document.getElementById('btnFullscreen'),
  toast: document.getElementById('toast')
};

// ----------------- App Lifecycle -----------------
document.addEventListener('DOMContentLoaded', () => {
  initWallpaperLoop();
  initEventListeners();
  updateWatchlistBadge();
  renderContinueWatching();
  loadHomepage();
});

// ----------------- Wallpaper Page-Refresh Loader -----------------
function initWallpaperLoop() {
  // Changes randomly ONLY when user refreshes / reloads the page (no interval timer)
  state.wallpaperIndex = Math.floor(Math.random() * WALLPAPERS.length);
  applyWallpaper(WALLPAPERS[state.wallpaperIndex]);
}

function applyWallpaper(url) {
  if (DOM.wallpaperLoopBg) {
    DOM.wallpaperLoopBg.style.backgroundImage = `url('${url}')`;
  }
  if (DOM.wallpaperBottomBg) {
    DOM.wallpaperBottomBg.style.backgroundImage = `url('${url}')`;
  }
}

// ----------------- Event Listeners -----------------
function initEventListeners() {
  // Navigation tabs (if navbar elements exist)
  if (DOM.navLinks) {
    DOM.navLinks.forEach(link => {
      link.addEventListener('click', (e) => {
        const tab = link.getAttribute('data-tab');
        handleNavigation(tab, true);
      });
    });
  }

  // Hero Navigation buttons (Home, Movies, TV Series, Watchlist)
  if (DOM.heroNavButtons) {
    DOM.heroNavButtons.forEach(btn => {
      btn.addEventListener('click', () => {
        const tab = btn.getAttribute('data-tab');
        handleNavigation(tab, true);
      });
    });
  }

  if (DOM.brandLogo) {
    DOM.brandLogo.addEventListener('click', (e) => {
      e.preventDefault();
      handleNavigation('home', false);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }

  if (DOM.btnQuickSearch) {
    DOM.btnQuickSearch.addEventListener('click', () => {
      if (DOM.searchInput) {
        DOM.searchInput.focus();
        DOM.searchInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    });
  }

  // Category filter pills in Catalog section
  document.querySelectorAll('#catalogSection .pill-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('#catalogSection .pill-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      state.activeFilter = btn.getAttribute('data-filter');
      filterAndRenderCatalog();
      scrollToCatalog();
    });
  });

  // Search input & autocomplete (always searches all engines)
  if (DOM.searchInput) {
    DOM.searchInput.addEventListener('input', handleSearchInput);
    DOM.searchInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        const q = DOM.searchInput.value.trim();
        if (q) {
          if (DOM.suggestionsDropdown) DOM.suggestionsDropdown.style.display = 'none';
          executeSearch(q, 'all');
        }
      }
    });
  }

  if (DOM.searchSubmitBtn) {
    DOM.searchSubmitBtn.addEventListener('click', () => {
      const q = DOM.searchInput.value.trim();
      if (q) {
        if (DOM.suggestionsDropdown) DOM.suggestionsDropdown.style.display = 'none';
        executeSearch(q, 'all');
      }
    });
  }

  if (DOM.searchClear) {
    DOM.searchClear.addEventListener('click', () => {
      DOM.searchInput.value = '';
      DOM.searchClear.style.display = 'none';
      if (DOM.suggestionsDropdown) DOM.suggestionsDropdown.style.display = 'none';
      if (state.activeTab === 'search') {
        handleNavigation('home', false);
      }
    });
  }

  // Quick genre tags (Telugu Dubbed, Marvel, Action, Trending Shows)
  if (DOM.quickGenreTags) {
    DOM.quickGenreTags.querySelectorAll('.genre-tag').forEach(tag => {
      tag.addEventListener('click', () => {
        DOM.quickGenreTags.querySelectorAll('.genre-tag').forEach(t => t.classList.remove('active'));
        tag.classList.add('active');
        const query = tag.getAttribute('data-query');
        if (query === 'telugu') {
          state.activeFilter = 'telugu';
          document.querySelectorAll('#catalogSection .pill-btn').forEach(b => b.classList.toggle('active', b.getAttribute('data-filter') === 'telugu'));
          filterAndRenderCatalog();
          scrollToCatalog();
        } else {
          DOM.searchInput.value = query;
          if (DOM.searchClear) DOM.searchClear.style.display = 'block';
          executeSearch(query, 'all');
        }
      });
    });
  }

  // Outside click listeners
  document.addEventListener('click', (e) => {
    if (!e.target.closest('.center-search-wrapper')) {
      DOM.suggestionsDropdown.style.display = 'none';
    }
    if (!e.target.closest('.dropdown-wrapper') && !e.target.closest('.audio-subtitles-drawer') && !e.target.closest('.hotstar-audio-btn')) {
      closeAllDropdowns();
    }
  });

  DOM.backToHomeBtn.addEventListener('click', () => handleNavigation('home', false));
  DOM.clearHistoryBtn.addEventListener('click', clearHistory);
  DOM.clearWatchlistBtn.addEventListener('click', clearWatchlist);

  // Details Modal actions
  DOM.modalCloseBtn.addEventListener('click', closeDetails);
  DOM.modalBackdrop.addEventListener('click', closeDetails);
  DOM.modalPlayBtn.addEventListener('click', () => {
    if (state.currentDetails) {
      startPlayback(state.currentDetails, state.activeDub, state.selectedSeason, state.selectedEpisode);
    }
  });
  DOM.modalDownloadBtn.addEventListener('click', () => {
    if (state.currentDetails) openDownloadModal(state.currentDetails, state.activeDub);
  });
  DOM.modalWatchlistBtn.addEventListener('click', () => {
    if (state.currentDetails) toggleWatchlist(state.currentDetails);
  });
  DOM.seasonSelect.addEventListener('change', (e) => {
    state.selectedSeason = parseInt(e.target.value);
    renderEpisodesForSeason(state.selectedSeason);
    previewStreamsAndSubtitles(
      state.activeDub ? state.activeDub.id : state.currentDetails.id,
      state.selectedSeason,
      state.selectedEpisode
    );
  });

  // Download Dialog Actions
  DOM.downloadModalCloseBtn.addEventListener('click', closeDownloadModal);
  DOM.downloadModalBackdrop.addEventListener('click', closeDownloadModal);
  DOM.btnCancelDownload.addEventListener('click', closeDownloadModal);
  DOM.btnConfirmDownload.addEventListener('click', executeDownload);

  // Player Controls
  DOM.playerCloseBtn.addEventListener('click', closePlayer);
  DOM.btnPlayPause.addEventListener('click', togglePlayPause);
  DOM.playerBigPlayBtn.addEventListener('click', togglePlayPause);
  DOM.btnRewind.addEventListener('click', () => seekRelative(-10));
  DOM.btnForward.addEventListener('click', () => seekRelative(10));
  DOM.btnVolume.addEventListener('click', toggleMute);
  DOM.volumeSlider.addEventListener('input', (e) => {
    DOM.videoElement.volume = parseFloat(e.target.value);
    DOM.videoElement.muted = (DOM.videoElement.volume === 0);
    updateVolumeIcon();
  });

  // Progress Seekbar
  DOM.progressContainer.addEventListener('click', seekToPosition);
  DOM.progressContainer.addEventListener('mousemove', handleProgressHover);
  DOM.progressContainer.addEventListener('mouseleave', () => {
    DOM.progressHoverTime.style.display = 'none';
  });

  // Audio & Subtitles Drawer
  DOM.btnAudioSubtitles.addEventListener('click', (e) => {
    e.stopPropagation();
    toggleAudioSubDrawer();
  });
  DOM.drawerCloseBtn.addEventListener('click', closeAudioSubDrawer);

  // Quality & Speed Dropdowns
  DOM.btnQuality.addEventListener('click', (e) => {
    e.stopPropagation();
    toggleDropdown(DOM.qualityMenu);
  });
  DOM.btnSpeed.addEventListener('click', (e) => {
    e.stopPropagation();
    toggleDropdown(DOM.speedMenu);
  });

  DOM.speedMenu.querySelectorAll('.dropdown-item').forEach(item => {
    item.addEventListener('click', () => {
      const speed = parseFloat(item.getAttribute('data-speed'));
      DOM.videoElement.playbackRate = speed;
      DOM.speedLabel.textContent = speed === 1.0 ? '1x' : `${speed}x`;
      DOM.speedMenu.querySelectorAll('.dropdown-item').forEach(i => i.classList.remove('active'));
      item.classList.add('active');
      DOM.speedMenu.classList.remove('active');
      showToast(`Playback speed: ${speed}x`);
    });
  });

  // In-Player Download Button
  DOM.btnPlayerDownload.addEventListener('click', () => {
    if (state.currentDetails) openDownloadModal(state.currentDetails, state.activeDub);
  });

  DOM.btnPiP.addEventListener('click', togglePictureInPicture);
  DOM.btnFullscreen.addEventListener('click', toggleFullscreen);
  DOM.btnNextEpisode.addEventListener('click', playNextEpisode);

  // Video Events
  DOM.videoElement.addEventListener('timeupdate', updateVideoProgress);
  DOM.videoElement.addEventListener('play', () => {
    state.isPlaying = true;
    DOM.btnPlayPause.innerHTML = '<i class="fa-solid fa-pause"></i>';
    DOM.playerBigPlayBtn.classList.remove('visible');
  });
  DOM.videoElement.addEventListener('pause', () => {
    state.isPlaying = false;
    DOM.btnPlayPause.innerHTML = '<i class="fa-solid fa-play"></i>';
    DOM.playerBigPlayBtn.classList.add('visible');
  });
  DOM.videoElement.addEventListener('waiting', () => {
    DOM.playerSpinner.classList.add('visible');
  });
  DOM.videoElement.addEventListener('canplay', () => {
    DOM.playerSpinner.classList.remove('visible');
  });
  DOM.videoElement.addEventListener('ended', handleVideoEnded);

  DOM.playerContainer.addEventListener('mousemove', resetControlsTimer);
  DOM.playerContainer.addEventListener('click', resetControlsTimer);

  document.addEventListener('keydown', handleKeyboardShortcuts);
}

// ----------------- Navigation & Scroll -----------------
function handleNavigation(tab, shouldScrollToCatalog = false) {
  state.activeTab = tab;
  
  if (DOM.navLinks) {
    DOM.navLinks.forEach(l => l.classList.toggle('active', l.getAttribute('data-tab') === tab));
  }
  if (DOM.heroNavButtons) {
    DOM.heroNavButtons.forEach(b => b.classList.toggle('active', b.getAttribute('data-tab') === tab));
  }

  DOM.homeView.style.display = 'none';
  DOM.searchResultsView.style.display = 'none';
  DOM.watchlistView.style.display = 'none';

  if (tab === 'home') {
    DOM.homeView.style.display = 'block';
    state.activeFilter = 'all';
    if (DOM.catalogHeaderTitle) DOM.catalogHeaderTitle.innerHTML = '<i class="fa-solid fa-fire"></i> Trending & Popular Titles';
    document.querySelectorAll('#catalogSection .pill-btn').forEach(b => b.classList.toggle('active', b.getAttribute('data-filter') === 'all'));
    filterAndRenderCatalog();
    if (shouldScrollToCatalog) scrollToCatalog();
  } else if (tab === 'movies') {
    DOM.homeView.style.display = 'block';
    state.activeFilter = 'movie';
    if (DOM.catalogHeaderTitle) DOM.catalogHeaderTitle.innerHTML = '<i class="fa-solid fa-film"></i> Movies (Feature Films)';
    document.querySelectorAll('#catalogSection .pill-btn').forEach(b => b.classList.toggle('active', b.getAttribute('data-filter') === 'movie'));
    filterAndRenderCatalog();
    if (shouldScrollToCatalog) scrollToCatalog();
  } else if (tab === 'series') {
    DOM.homeView.style.display = 'block';
    state.activeFilter = 'series';
    if (DOM.catalogHeaderTitle) DOM.catalogHeaderTitle.innerHTML = '<i class="fa-solid fa-tv"></i> TV Series & Shows';
    document.querySelectorAll('#catalogSection .pill-btn').forEach(b => b.classList.toggle('active', b.getAttribute('data-filter') === 'series'));
    filterAndRenderCatalog();
    if (shouldScrollToCatalog) scrollToCatalog();
  } else if (tab === 'watchlist') {
    DOM.watchlistView.style.display = 'block';
    renderWatchlistView();
    DOM.watchlistView.scrollIntoView({ behavior: 'smooth' });
  } else if (tab === 'search') {
    DOM.searchResultsView.style.display = 'block';
    DOM.searchResultsView.scrollIntoView({ behavior: 'smooth' });
  }
}

function scrollToCatalog() {
  if (DOM.catalogSection) {
    DOM.catalogSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}

// ----------------- Data Fetching -----------------
async function loadHomepage() {
  try {
    const res = await fetch('/api/homepage?tab=all&page=1');
    const data = await res.json();
    if (data.success && data.items.length > 0) {
      state.catalogItems = data.items;
      filterAndRenderCatalog();
    } else {
      DOM.trendingGrid.innerHTML = `<div class="empty-state"><h3>No titles found</h3></div>`;
    }
  } catch (err) {
    console.error('Failed to load homepage:', err);
    DOM.trendingGrid.innerHTML = `<div class="empty-state"><h3>Failed to load content</h3><p>${escapeHtml(err.message)}</p></div>`;
  }
}

function filterAndRenderCatalog() {
  let filtered = state.catalogItems;
  if (state.activeFilter === 'movie') {
    filtered = filtered.filter(i => !i.is_series);
  } else if (state.activeFilter === 'series') {
    filtered = filtered.filter(i => i.is_series);
  } else if (state.activeFilter === 'telugu') {
    filtered = filtered.filter(i => 
      (i.raw_title && i.raw_title.toLowerCase().includes('telugu')) ||
      (i.title && i.title.toLowerCase().includes('telugu'))
    );
    if (filtered.length === 0) {
      // Fallback search for telugu
      executeSearch("Telugu", "all");
      return;
    }
  }
  renderGrid(DOM.trendingGrid, filtered);
}

function renderGrid(container, items) {
  if (!items || items.length === 0) {
    container.innerHTML = `<div class="empty-state"><h3>No items found</h3></div>`;
    return;
  }

  container.innerHTML = items.map(item => `
    <div class="media-card" data-id="${item.id}">
      <div class="poster-wrapper">
        <img class="poster-img" src="${item.poster_url || '/static/placeholder.jpg'}" alt="${escapeHtml(item.title)}" loading="lazy" onerror="this.src='https://placehold.co/300x450/151a27/9da8b6?text=No+Poster'">
        <span class="card-type-badge">${item.is_series ? 'SERIES' : 'MOVIE'}</span>
        ${item.rating ? `<span class="card-rating"><i class="fa-solid fa-star"></i> ${item.rating}</span>` : ''}
        <div class="card-play-overlay">
          <div class="card-play-btn"><i class="fa-solid fa-play"></i></div>
        </div>
      </div>
      <div class="card-info">
        <h4 class="card-title" title="${escapeHtml(item.title)}">${escapeHtml(item.title)}</h4>
        <div class="card-meta">
          <span>${item.year || ''}</span>
          <span>${item.duration || ''}</span>
        </div>
      </div>
    </div>
  `).join('');

  container.querySelectorAll('.media-card').forEach(card => {
    card.addEventListener('click', () => {
      const id = card.getAttribute('data-id');
      openDetails(id);
    });
  });
}

// ----------------- Multi-Engine Search & Rich Poster Autocomplete -----------------
function handleSearchInput() {
  const query = DOM.searchInput.value.trim();
  DOM.searchClear.style.display = query ? 'block' : 'none';

  clearTimeout(state.searchTimeout);
  if (!query || query.length < 2) {
    DOM.suggestionsDropdown.style.display = 'none';
    return;
  }

  state.searchTimeout = setTimeout(async () => {
    try {
      const res = await fetch(`/api/suggest?q=${encodeURIComponent(query)}&provider=all`);
      const data = await res.json();
      if (data.success && data.suggestions.length > 0) {
        renderRichSuggestions(data.suggestions);
      } else {
        DOM.suggestionsDropdown.style.display = 'none';
      }
    } catch (err) {
      console.warn('Suggest error:', err);
    }
  }, 220);
}

function renderRichSuggestions(suggestions) {
  DOM.suggestionsDropdown.innerHTML = suggestions.map(s => `
    <div class="suggestion-card" data-id="${s.id}">
      <img class="suggest-thumb" src="${s.poster_url || '/static/placeholder.jpg'}" alt="${escapeHtml(s.title)}" onerror="this.src='https://placehold.co/100x150/151a27/9da8b6?text=Thumb'">
      <div class="suggest-info">
        <div class="suggest-title">${escapeHtml(s.title)}</div>
        <div class="suggest-meta">
          <span>${s.is_series ? 'TV Series' : 'Movie'}</span>
          ${s.year ? `<span>• ${s.year}</span>` : ''}
          ${s.rating ? `<span>• <i class="fa-solid fa-star" style="color:#f5c518;font-size:0.7rem;"></i> ${s.rating}</span>` : ''}
        </div>
      </div>
    </div>
  `).join('');

  DOM.suggestionsDropdown.querySelectorAll('.suggestion-card').forEach(item => {
    item.addEventListener('click', () => {
      const id = item.getAttribute('data-id');
      DOM.suggestionsDropdown.style.display = 'none';
      openDetails(id);
    });
  });

  DOM.suggestionsDropdown.style.display = 'block';
}

async function executeSearch(query, provider = 'all') {
  if (!query) return;
  handleNavigation('search', false);
  DOM.searchHeaderTitle.innerHTML = `<i class="fa-solid fa-magnifying-glass"></i> Search: "${escapeHtml(query)}"`;
  DOM.searchGrid.innerHTML = `<div class="loading-spinner"><div class="spinner"></div><p>Searching across all engines...</p></div>`;
  DOM.searchResultsView.scrollIntoView({ behavior: 'smooth', block: 'start' });

  try {
    const res = await fetch(`/api/search?q=${encodeURIComponent(query)}&provider=${encodeURIComponent(provider)}`);
    const data = await res.json();
    if (data.success && data.items.length > 0) {
      renderGrid(DOM.searchGrid, data.items);
    } else {
      DOM.searchGrid.innerHTML = `
        <div class="empty-state">
          <i class="fa-solid fa-film empty-icon"></i>
          <h3>No results found for "${escapeHtml(query)}"</h3>
          <p>Try selecting "All Engines" or checking spelling.</p>
        </div>
      `;
    }
  } catch (err) {
    DOM.searchGrid.innerHTML = `<div class="empty-state"><h3>Search failed: ${escapeHtml(err.message)}</h3></div>`;
  }
}

// ----------------- Disney+ / Hotstar Details Modal -----------------
async function openDetails(subjectId, autoPlay = false, targetDubId = null) {
  DOM.detailsModal.classList.add('active');
  DOM.modalTitle.textContent = "Loading...";
  DOM.modalDescription.textContent = "";
  DOM.modalAudioChipsGrid.innerHTML = `<div style="color: #8fa0b5; font-size: 0.88rem;"><i class="fa-solid fa-spinner fa-spin"></i> Loading available audio languages...</div>`;
  DOM.streamQualitiesList.innerHTML = `<div class="loading-stream-info"><i class="fa-solid fa-spinner fa-spin"></i> Checking available stream qualities...</div>`;
  DOM.modalSubtitlesList.innerHTML = `<span style="color: #8fa0b5; font-size: 0.85rem;">Checking subtitles...</span>`;

  try {
    const res = await fetch(`/api/details?id=${subjectId}`);
    const data = await res.json();
    if (!data.success) throw new Error(data.error || 'Failed to fetch details');

    const details = data.details;
    state.currentDetails = details;
    state.selectedSeason = 1;
    state.selectedEpisode = 1;

    DOM.modalTitle.textContent = details.title;
    DOM.modalType.textContent = details.is_series ? 'TV SERIES' : 'MOVIE';
    if (DOM.modalProvider) DOM.modalProvider.textContent = details.provider || 'MOVIETAP';
    DOM.modalRating.innerHTML = `<i class="fa-solid fa-star"></i> ${details.rating || '8.5'}`;
    DOM.modalYear.textContent = details.year || '';
    DOM.modalDuration.textContent = details.duration || '';
    DOM.modalGenres.textContent = (details.genres && details.genres.length) ? details.genres.join(', ') : 'Cinema';
    DOM.modalDescription.textContent = details.description || 'No overview available.';

    if (details.director) {
      DOM.modalDirectorRow.style.display = 'flex';
      DOM.modalDirector.textContent = details.director;
    } else {
      DOM.modalDirectorRow.style.display = 'none';
    }

    if (details.stars) {
      DOM.modalStarsRow.style.display = 'flex';
      DOM.modalStars.textContent = details.stars;
    } else {
      DOM.modalStarsRow.style.display = 'none';
    }

    if (details.poster_url) {
      DOM.modalPoster.src = details.poster_url;
      DOM.modalHeroBg.style.backgroundImage = `url('${details.poster_url}')`;
    }

    const isSaved = state.watchlist.some(w => w.id === details.id);
    DOM.modalWatchlistBtn.innerHTML = isSaved
      ? '<i class="fa-solid fa-bookmark"></i> In Watchlist'
      : '<i class="fa-regular fa-bookmark"></i> Add to Watchlist';

    // TV Series Handling
    if (details.is_series && details.seasons && details.seasons.length > 0) {
      DOM.modalSeriesSection.style.display = 'block';
      DOM.seasonSelect.innerHTML = details.seasons.map(s => `
        <option value="${s.season}">Season ${s.season}</option>
      `).join('');
      state.selectedSeason = details.seasons[0].season;
      renderEpisodesForSeason(state.selectedSeason);
    } else {
      DOM.modalSeriesSection.style.display = 'none';
    }

    // Audio Dubs (Prioritize Telugu!)
    const dubs = (details.dubs && details.dubs.length > 0)
      ? details.dubs
      : [{ id: details.id, title: details.title, language: 'Original Audio', is_current: true }];

    let activeDub = null;
    if (targetDubId) {
      activeDub = dubs.find(d => String(d.id) === String(targetDubId));
    }
    if (!activeDub) {
      // Prioritize Telugu first, then Hindi, then current/first
      activeDub = dubs.find(d => d.language.toLowerCase().includes('telugu'))
               || dubs.find(d => d.language.toLowerCase().includes('hindi'))
               || dubs.find(d => d.is_current)
               || dubs[0];
    }
    state.activeDub = activeDub;

    renderAudioLanguageChips(dubs, activeDub.id);
    updateModalPlayButton(activeDub.language);

    // Preview stream qualities and subtitles
    await previewStreamsAndSubtitles(
      activeDub.id,
      details.is_series ? state.selectedSeason : 0,
      details.is_series ? state.selectedEpisode : 0
    );

    if (autoPlay) {
      startPlayback(details, state.activeDub, state.selectedSeason, state.selectedEpisode);
    }

  } catch (err) {
    console.error('Error opening details:', err);
    DOM.modalTitle.textContent = "Error Loading Details";
    DOM.modalDescription.textContent = err.message;
  }
}

function renderAudioLanguageChips(dubs, activeDubId) {
  DOM.audioLanguagesCount.textContent = `${dubs.length} Language${dubs.length > 1 ? 's' : ''}`;

  DOM.modalAudioChipsGrid.innerHTML = dubs.map(dub => {
    const isActive = String(dub.id) === String(activeDubId);
    return `
      <button class="lang-chip ${isActive ? 'active' : ''}" data-dub-id="${dub.id}" data-dub-lang="${escapeHtml(dub.language)}">
        <i class="fa-solid fa-headphones"></i>
        <span>${escapeHtml(dub.language)}</span>
        ${isActive ? '<i class="fa-solid fa-check check-icon"></i>' : ''}
      </button>
    `;
  }).join('');

  DOM.modalAudioChipsGrid.querySelectorAll('.lang-chip').forEach(btn => {
    btn.addEventListener('click', () => {
      const dubId = btn.getAttribute('data-dub-id');
      const dub = (state.currentDetails.dubs || []).find(d => String(d.id) === String(dubId)) || {
        id: dubId,
        language: btn.getAttribute('data-dub-lang')
      };
      selectDub(dub);
    });
  });
}

function selectDub(dub) {
  state.activeDub = dub;
  renderAudioLanguageChips(state.currentDetails.dubs || [dub], dub.id);
  updateModalPlayButton(dub.language);
  showToast(`Selected audio: ${dub.language}`);

  previewStreamsAndSubtitles(
    dub.id,
    state.currentDetails.is_series ? state.selectedSeason : 0,
    state.currentDetails.is_series ? state.selectedEpisode : 0
  );
}

function updateModalPlayButton(language) {
  DOM.modalPlayBtn.innerHTML = `<i class="fa-solid fa-play"></i> Watch in ${escapeHtml(language || 'Telugu')}`;
}

function renderEpisodesForSeason(seasonNum) {
  if (!state.currentDetails) return;
  const seasonObj = state.currentDetails.seasons.find(s => s.season === seasonNum);
  if (!seasonObj) return;

  DOM.episodeGrid.innerHTML = seasonObj.episodes.map(ep => `
    <button class="ep-btn ${ep.episode === state.selectedEpisode ? 'active' : ''}" data-ep="${ep.episode}">
      <span class="ep-num">EP ${ep.episode}</span>
      <span class="ep-play-label"><i class="fa-solid fa-play"></i> Play</span>
    </button>
  `).join('');

  DOM.episodeGrid.querySelectorAll('.ep-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      DOM.episodeGrid.querySelectorAll('.ep-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      state.selectedEpisode = parseInt(btn.getAttribute('data-ep'));
      
      previewStreamsAndSubtitles(
        state.activeDub ? state.activeDub.id : state.currentDetails.id,
        state.selectedSeason,
        state.selectedEpisode
      );
      startPlayback(state.currentDetails, state.activeDub, state.selectedSeason, state.selectedEpisode);
    });
  });
}

async function previewStreamsAndSubtitles(subjectId, season = 0, episode = 0) {
  DOM.streamQualitiesList.innerHTML = `<div class="loading-stream-info"><i class="fa-solid fa-spinner fa-spin"></i> Checking stream qualities...</div>`;
  DOM.modalSubtitlesList.innerHTML = `<span style="color: #8fa0b5; font-size: 0.85rem;">Checking subtitles...</span>`;

  try {
    const res = await fetch(`/api/streams?id=${subjectId}&season=${season}&episode=${episode}`);
    const data = await res.json();
    if (data.success && data.streams.length > 0) {
      state.currentStreams = data.streams;
      DOM.qualitiesCount.textContent = `${data.streams.length} Available`;
      DOM.streamQualitiesList.innerHTML = data.streams.map(s => `
        <div class="quality-chip">
          <i class="fa-solid fa-circle-check" style="color: #46d369;"></i>
          <span class="res">${s.quality}</span>
          ${s.size_formatted ? `<span class="size">${s.size_formatted}</span>` : ''}
          <span class="badge" style="font-size: 0.65rem; color: #8fa0b5;">${(s.codec || 'H264').toUpperCase()}</span>
        </div>
      `).join('');

      const topStream = data.streams[0];
      if (topStream && topStream.resource_id) {
        fetchSubtitlesPreview(subjectId, topStream.resource_id);
      } else {
        DOM.modalSubtitlesList.innerHTML = `<span style="color: #8fa0b5; font-size: 0.85rem;">Subtitles ready during playback.</span>`;
        DOM.subtitlesCount.textContent = `0 Available`;
      }
    } else {
      DOM.qualitiesCount.textContent = `0 Available`;
      DOM.streamQualitiesList.innerHTML = `<span style="color: #8fa0b5; font-size: 0.9rem;">Direct streams will resolve automatically upon playback.</span>`;
    }
  } catch (err) {
    DOM.streamQualitiesList.innerHTML = `<span style="color: #ff5c5c; font-size: 0.85rem;">Could not preview streams: ${escapeHtml(err.message)}</span>`;
  }
}

async function fetchSubtitlesPreview(subjectId, resourceId) {
  try {
    const res = await fetch(`/api/captions?id=${subjectId}&rid=${resourceId}`);
    const data = await res.json();
    if (data.success && data.captions.length > 0) {
      state.currentCaptions = data.captions;
      DOM.subtitlesCount.textContent = `${data.captions.length} Available`;
      DOM.modalSubtitlesList.innerHTML = data.captions.slice(0, 8).map(c => `
        <span class="quality-chip" style="font-size: 0.8rem; padding: 4px 10px;">
          <i class="fa-solid fa-closed-captioning" style="color: #0072d2;"></i> ${escapeHtml(c.language)}
        </span>
      `).join('');
    } else {
      DOM.subtitlesCount.textContent = `0 Available`;
      DOM.modalSubtitlesList.innerHTML = `<span style="color: #8fa0b5; font-size: 0.85rem;">No external subtitles found for this audio track.</span>`;
    }
  } catch (err) {
    DOM.modalSubtitlesList.innerHTML = `<span style="color: #8fa0b5; font-size: 0.85rem;">Subtitles check unavailable.</span>`;
  }
}

function closeDetails() {
  DOM.detailsModal.classList.remove('active');
}

// ----------------- Download Modal & In-Browser Download -----------------
function openDownloadModal(media, dub) {
  DOM.downloadMediaTitle.textContent = `Download "${media.title}"`;
  const activeDub = dub || state.activeDub || { id: media.id, language: 'Telugu' };
  state.downloadDub = activeDub;

  DOM.downloadModal.classList.add('active');

  // Populate Languages
  const dubs = (media.dubs && media.dubs.length > 0)
    ? media.dubs
    : [{ id: media.id, language: 'Original Audio' }];

  DOM.downloadLangChips.innerHTML = dubs.map(d => {
    const isAct = String(d.id) === String(activeDub.id);
    return `<button class="download-chip ${isAct ? 'active' : ''}" data-id="${d.id}" data-lang="${escapeHtml(d.language)}">${escapeHtml(d.language)}</button>`;
  }).join('');

  DOM.downloadLangChips.querySelectorAll('.download-chip').forEach(btn => {
    btn.addEventListener('click', () => {
      DOM.downloadLangChips.querySelectorAll('.download-chip').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const dId = btn.getAttribute('data-id');
      state.downloadDub = dubs.find(d => String(d.id) === String(dId)) || { id: dId, language: btn.getAttribute('data-lang') };
      loadDownloadStreamsAndSubs(state.downloadDub.id);
    });
  });

  loadDownloadStreamsAndSubs(activeDub.id);
}

async function loadDownloadStreamsAndSubs(subjectId) {
  DOM.downloadQualityChips.innerHTML = `<div style="color:#8fa0b5;font-size:0.85rem;"><i class="fa-solid fa-spinner fa-spin"></i> Checking stream qualities...</div>`;
  DOM.downloadSubtitleChips.innerHTML = `<button class="download-chip active" data-sub="none">No Subtitle (None)</button>`;

  try {
    const sNum = state.currentDetails && state.currentDetails.is_series ? state.selectedSeason : 0;
    const epNum = state.currentDetails && state.currentDetails.is_series ? state.selectedEpisode : 0;
    const res = await fetch(`/api/streams?id=${subjectId}&season=${sNum}&episode=${epNum}`);
    const data = await res.json();
    if (data.success && data.streams.length > 0) {
      state.downloadStream = data.streams[0];
      DOM.downloadQualityChips.innerHTML = data.streams.map((s, idx) => `
        <button class="download-chip ${idx === 0 ? 'active' : ''}" data-idx="${idx}">
          ${s.quality} ${s.size_formatted ? `(${s.size_formatted})` : ''}
        </button>
      `).join('');

      DOM.downloadQualityChips.querySelectorAll('.download-chip').forEach(btn => {
        btn.addEventListener('click', () => {
          DOM.downloadQualityChips.querySelectorAll('.download-chip').forEach(b => b.classList.remove('active'));
          btn.classList.add('active');
          const idx = parseInt(btn.getAttribute('data-idx'));
          state.downloadStream = data.streams[idx];
        });
      });

      // Load Subtitles for download options
      if (data.streams[0].resource_id) {
        const subRes = await fetch(`/api/captions?id=${subjectId}&rid=${data.streams[0].resource_id}`);
        const subData = await subRes.json();
        let subHtml = `<button class="download-chip active" data-sub="none">No Subtitle (None)</button>`;
        if (subData.success && subData.captions.length > 0) {
          subHtml += subData.captions.map((c, idx) => `
            <button class="download-chip" data-sub-idx="${idx}">${escapeHtml(c.language)} (.srt)</button>
          `).join('');
        }
        DOM.downloadSubtitleChips.innerHTML = subHtml;

        state.downloadCaption = null;
        DOM.downloadSubtitleChips.querySelectorAll('.download-chip').forEach(btn => {
          btn.addEventListener('click', () => {
            DOM.downloadSubtitleChips.querySelectorAll('.download-chip').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            if (btn.getAttribute('data-sub') === 'none') {
              state.downloadCaption = null;
            } else {
              const idx = parseInt(btn.getAttribute('data-sub-idx'));
              state.downloadCaption = subData.captions[idx];
            }
          });
        });
      }
    } else {
      DOM.downloadQualityChips.innerHTML = `<span style="color:#ff5c5c;font-size:0.85rem;">No download mirrors found.</span>`;
    }
  } catch (err) {
    DOM.downloadQualityChips.innerHTML = `<span style="color:#ff5c5c;font-size:0.85rem;">Error: ${err.message}</span>`;
  }
}

function closeDownloadModal() {
  DOM.downloadModal.classList.remove('active');
}

function executeDownload() {
  if (!state.downloadStream) {
    showToast("Please choose a quality to download.");
    return;
  }

  const mediaTitle = state.currentDetails ? state.currentDetails.title : "MovieTap_Video";
  const lang = state.downloadDub ? state.downloadDub.language : "Audio";
  const qual = state.downloadStream.quality;
  const subLang = (state.downloadCaption && state.downloadCaption.language) ? `_[${state.downloadCaption.language}Subs]` : '';
  const filename = `${mediaTitle}_[${lang}]_[${qual}]${subLang}`.replace(/[/\\?%*:|"<>]/g, '_');

  let downloadUrl = `/api/download?url=${encodeURIComponent(state.downloadStream.url)}&filename=${encodeURIComponent(filename)}`;
  if (state.downloadCaption && state.downloadCaption.url) {
    downloadUrl += `&subtitle_url=${encodeURIComponent(state.downloadCaption.url)}`;
  }
  
  // Trigger single browser download with embedded subtitles
  const a = document.createElement('a');
  a.href = downloadUrl;
  a.download = `${filename}.mp4`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);

  if (state.downloadCaption && state.downloadCaption.language) {
    showToast(`Downloading "${mediaTitle}" with ${state.downloadCaption.language} subtitles embedded inside video!`);
  } else {
    showToast(`Downloading "${mediaTitle}" (${qual}). Check browser downloads!`);
  }

  closeDownloadModal();
}

// ----------------- Disney+ / Hotstar Video Player -----------------
async function startPlayback(media, dub, season = 0, episode = 0) {
  closeDetails();
  DOM.playerModal.classList.add('active');

  // Default to Telugu if not specified
  let activeDub = dub || state.activeDub;
  if (!activeDub && media.dubs && media.dubs.length > 0) {
    activeDub = media.dubs.find(d => d.language.toLowerCase().includes('telugu'))
             || media.dubs.find(d => d.language.toLowerCase().includes('hindi'))
             || media.dubs[0];
  }
  if (!activeDub) {
    activeDub = { id: media.id, language: 'Telugu' };
  }
  state.activeDub = activeDub;

  DOM.playerMediaTitle.textContent = media.title;
  let subTitleStr = media.year ? `(${media.year})` : '';
  if (media.is_series && episode > 0) {
    subTitleStr = `Season ${season} • Episode ${episode}`;
    DOM.btnNextEpisode.style.display = 'flex';
  } else {
    DOM.btnNextEpisode.style.display = 'none';
  }
  DOM.playerMediaSubtitle.textContent = subTitleStr;

  DOM.playerAudioBadge.innerHTML = `<i class="fa-solid fa-headphones"></i> ${escapeHtml(activeDub.language)}`;
  DOM.playerQualityBadge.innerHTML = `<i class="fa-solid fa-gear"></i> Loading...`;

  DOM.playerSpinner.classList.add('visible');
  DOM.playerBigPlayBtn.classList.remove('visible');

  // Populate Hotstar Audio Drawer
  const dubs = (media.dubs && media.dubs.length > 0)
    ? media.dubs
    : [{ id: media.id, title: media.title, language: 'Original Audio', is_current: true }];
  populateAudioDrawer(dubs, activeDub.id);

  try {
    const sNum = media.is_series ? season : 0;
    const epNum = media.is_series ? episode : 0;
    const res = await fetch(`/api/streams?id=${activeDub.id}&season=${sNum}&episode=${epNum}`);
    const data = await res.json();
    if (!data.success || data.streams.length === 0) {
      throw new Error(`No streams available for "${activeDub.language}". Try another audio track.`);
    }

    state.currentStreams = data.streams;
    const topStream = data.streams[0];
    state.activeStream = topStream;

    DOM.playerQualityBadge.innerHTML = `<i class="fa-solid fa-gear"></i> ${topStream.quality}`;
    populateQualityOptions(data.streams, topStream);

    loadSubtitlesForPlayer(activeDub.id, topStream.resource_id);

    const historyItem = state.watchHistory.find(h =>
      h.id === media.id && (!media.is_series || (h.season === season && h.episode === episode))
    );
    const resumeTime = (historyItem && historyItem.currentTime > 15) ? historyItem.currentTime : 0;

    playStream(topStream.proxy_url, resumeTime);

  } catch (err) {
    console.error('Playback error:', err);
    DOM.playerSpinner.classList.remove('visible');
    showToast(`Playback Error: ${err.message}`);
  }
}

function playStream(streamUrl, startTime = 0) {
  // Clear any existing tracks
  while (DOM.videoElement.getElementsByTagName('track').length > 0) {
    DOM.videoElement.removeChild(DOM.videoElement.getElementsByTagName('track')[0]);
  }
  DOM.subtitleOverlay.textContent = '';

  DOM.videoElement.src = streamUrl;
  DOM.videoElement.currentTime = startTime;

  DOM.videoElement.play().catch(err => {
    console.warn("Autoplay blocked or awaiting gesture:", err);
    DOM.playerBigPlayBtn.classList.add('visible');
  });

  if (startTime > 0) {
    showToast(`Resumed from ${formatTime(startTime)}`);
  }
}

// ----------------- In-Player Audio Switching -----------------
function populateAudioDrawer(dubs, activeDubId) {
  DOM.drawerAudioList.innerHTML = dubs.map(dub => {
    const isActive = String(dub.id) === String(activeDubId);
    return `
      <button class="drawer-item ${isActive ? 'active' : ''}" data-dub-id="${dub.id}" data-dub-lang="${escapeHtml(dub.language)}">
        <span>${escapeHtml(dub.language)}</span>
        ${isActive ? '<i class="fa-solid fa-check check"></i>' : ''}
      </button>
    `;
  }).join('');

  DOM.drawerAudioList.querySelectorAll('.drawer-item').forEach(btn => {
    btn.addEventListener('click', () => {
      const dubId = btn.getAttribute('data-dub-id');
      const dub = dubs.find(d => String(d.id) === String(dubId)) || {
        id: dubId,
        language: btn.getAttribute('data-dub-lang')
      };
      switchAudioLanguageInPlayer(dub);
    });
  });
}

async function switchAudioLanguageInPlayer(newDub) {
  if (state.activeDub && String(state.activeDub.id) === String(newDub.id)) {
    closeAudioSubDrawer();
    return;
  }

  showToast(`Switching audio to ${newDub.language}...`);
  const currentTimestamp = DOM.videoElement.currentTime || 0;
  const wasPlaying = !DOM.videoElement.paused;
  const prevQuality = state.activeStream ? state.activeStream.quality : '1080p';

  DOM.playerSpinner.classList.add('visible');

  try {
    const sNum = state.currentDetails && state.currentDetails.is_series ? state.selectedSeason : 0;
    const epNum = state.currentDetails && state.currentDetails.is_series ? state.selectedEpisode : 0;
    const res = await fetch(`/api/streams?id=${newDub.id}&season=${sNum}&episode=${epNum}`);
    const data = await res.json();
    if (!data.success || data.streams.length === 0) {
      throw new Error(`No streams available for audio track: ${newDub.language}`);
    }

    state.activeDub = newDub;
    state.currentStreams = data.streams;

    let chosenStream = data.streams.find(s => s.quality === prevQuality) || data.streams[0];
    state.activeStream = chosenStream;

    DOM.playerAudioBadge.innerHTML = `<i class="fa-solid fa-headphones"></i> ${escapeHtml(newDub.language)}`;
    DOM.playerQualityBadge.innerHTML = `<i class="fa-solid fa-gear"></i> ${chosenStream.quality}`;
    populateQualityOptions(data.streams, chosenStream);

    const allDubs = (state.currentDetails && state.currentDetails.dubs && state.currentDetails.dubs.length > 0)
      ? state.currentDetails.dubs
      : [newDub];
    populateAudioDrawer(allDubs, newDub.id);

    DOM.videoElement.src = chosenStream.proxy_url;
    DOM.videoElement.currentTime = currentTimestamp;
    if (wasPlaying) {
      DOM.videoElement.play();
    }

    loadSubtitlesForPlayer(newDub.id, chosenStream.resource_id);
    showToast(`Now playing in ${newDub.language}`);

  } catch (err) {
    console.error('Audio switch error:', err);
    DOM.playerSpinner.classList.remove('visible');
    showToast(`Audio switch failed: ${err.message}`);
  }
}

function toggleAudioSubDrawer() {
  const isOpen = DOM.audioSubDrawer.classList.contains('active');
  if (isOpen) {
    closeAudioSubDrawer();
  } else {
    openAudioSubDrawer();
  }
}

function openAudioSubDrawer() {
  closeAllDropdowns();
  DOM.audioSubDrawer.classList.add('active');
}

function closeAudioSubDrawer() {
  DOM.audioSubDrawer.classList.remove('active');
}

// ----------------- Fixed Subtitle Engine (No Duplicates) -----------------
async function loadSubtitlesForPlayer(subjectId, resourceId) {
  try {
    const res = await fetch(`/api/captions?id=${subjectId}&rid=${resourceId}`);
    const data = await res.json();
    if (data.success && data.captions.length > 0) {
      state.currentCaptions = data.captions;
      populateSubtitlesDrawer(data.captions);
    } else {
      state.currentCaptions = [];
      populateSubtitlesDrawer([]);
    }
  } catch (err) {
    console.warn('Subtitles fetch error:', err);
    state.currentCaptions = [];
    populateSubtitlesDrawer([]);
  }
}

function populateSubtitlesDrawer(captions) {
  const isOffActive = !state.activeCaption;

  let itemsHtml = `
    <button class="drawer-item ${isOffActive ? 'active' : ''}" data-sub="off">
      <span>Off</span>
      ${isOffActive ? '<i class="fa-solid fa-check check"></i>' : ''}
    </button>
  `;

  if (captions.length === 0) {
    itemsHtml += `<div style="color: #8fa0b5; font-size: 0.8rem; padding: 10px;">No external subtitles available</div>`;
  } else {
    itemsHtml += captions.map((c, idx) => {
      const isActive = state.activeCaption && state.activeCaption.url === c.url;
      return `
        <button class="drawer-item ${isActive ? 'active' : ''}" data-sub-idx="${idx}">
          <span>${escapeHtml(c.language)}</span>
          ${isActive ? '<i class="fa-solid fa-check check"></i>' : ''}
        </button>
      `;
    }).join('');
  }

  DOM.drawerSubtitlesList.innerHTML = itemsHtml;

  DOM.drawerSubtitlesList.querySelectorAll('.drawer-item').forEach(btn => {
    btn.addEventListener('click', () => {
      if (btn.getAttribute('data-sub') === 'off') {
        disableSubtitles();
      } else {
        const idx = parseInt(btn.getAttribute('data-sub-idx'));
        enableSubtitle(captions[idx]);
      }
      populateSubtitlesDrawer(state.currentCaptions);
    });
  });
}

function enableSubtitle(caption) {
  state.activeCaption = caption;

  // Clear existing tracks
  while (DOM.videoElement.getElementsByTagName('track').length > 0) {
    DOM.videoElement.removeChild(DOM.videoElement.getElementsByTagName('track')[0]);
  }
  DOM.subtitleOverlay.textContent = '';

  const track = document.createElement('track');
  track.kind = 'subtitles';
  track.label = caption.language;
  track.srclang = caption.code || 'en';
  track.src = caption.vtt_url;
  track.default = true;

  DOM.videoElement.appendChild(track);

  // KEY FIX: Set mode to 'hidden' so the browser native subtitle renderer is suppressed!
  // This completely eliminates the duplicate subtitle bug while letting JS read activeCues.
  track.addEventListener('load', () => {
    track.mode = 'hidden';
    if (DOM.videoElement.textTracks && DOM.videoElement.textTracks[0]) {
      DOM.videoElement.textTracks[0].mode = 'hidden';
      
      DOM.videoElement.textTracks[0].oncuechange = function() {
        const cues = this.activeCues;
        if (cues && cues.length > 0) {
          // Render only unique lines to prevent any in-VTT duplicate lines
          const rawLines = cues[0].text.split('\n');
          const cleanLines = Array.from(new Set(rawLines.map(l => l.replace(/<[^>]*>/g, '').trim()))).filter(Boolean);
          DOM.subtitleOverlay.textContent = cleanLines.join('\n');
        } else {
          DOM.subtitleOverlay.textContent = '';
        }
      };
    }
  });

  showToast(`Subtitles: ${caption.language}`);
}

function disableSubtitles() {
  state.activeCaption = null;
  DOM.subtitleOverlay.textContent = '';
  for (let i = 0; i < DOM.videoElement.textTracks.length; i++) {
    DOM.videoElement.textTracks[i].mode = 'disabled';
  }
  showToast('Subtitles Off');
}

// ----------------- Quality Switching -----------------
function populateQualityOptions(streams, activeStream) {
  DOM.qualityBadgeLabel.textContent = activeStream.quality;
  DOM.qualityOptionsList.innerHTML = streams.map(s => `
    <button class="dropdown-item ${s.url === activeStream.url ? 'active' : ''}" data-url="${escapeHtml(s.url)}">
      <span>${s.quality}</span>
      <span style="font-size: 0.75rem; color: #8fa0b5;">${s.size_formatted || ''}</span>
    </button>
  `).join('');

  DOM.qualityOptionsList.querySelectorAll('.dropdown-item').forEach((btn, idx) => {
    btn.addEventListener('click', () => {
      switchQuality(streams[idx]);
    });
  });
}

function switchQuality(newStream) {
  if (state.activeStream && state.activeStream.url === newStream.url) {
    DOM.qualityMenu.classList.remove('active');
    return;
  }

  const currentTime = DOM.videoElement.currentTime;
  const wasPlaying = !DOM.videoElement.paused;

  state.activeStream = newStream;
  DOM.qualityBadgeLabel.textContent = newStream.quality;
  DOM.playerQualityBadge.innerHTML = `<i class="fa-solid fa-gear"></i> ${newStream.quality}`;

  DOM.qualityOptionsList.querySelectorAll('.dropdown-item').forEach(item => {
    item.classList.toggle('active', item.getAttribute('data-url') === newStream.url);
  });
  DOM.qualityMenu.classList.remove('active');

  DOM.videoElement.src = newStream.proxy_url;
  DOM.videoElement.currentTime = currentTime;
  if (wasPlaying) {
    DOM.videoElement.play();
  }
  showToast(`Quality switched to ${newStream.quality}`);
}

// ----------------- Core Player Controls & Seekbar -----------------
function closePlayer() {
  saveCurrentProgress();
  DOM.videoElement.pause();
  DOM.videoElement.src = '';
  DOM.subtitleOverlay.textContent = '';
  DOM.playerModal.classList.remove('active');
  closeAudioSubDrawer();
  closeAllDropdowns();
  renderContinueWatching();
}

function togglePlayPause() {
  if (DOM.videoElement.paused) {
    DOM.videoElement.play();
  } else {
    DOM.videoElement.pause();
  }
}

function seekRelative(seconds) {
  const cur = DOM.videoElement.currentTime || 0;
  const dur = DOM.videoElement.duration || 0;
  DOM.videoElement.currentTime = Math.max(0, Math.min(dur, cur + seconds));
}

function seekToPosition(e) {
  const rect = DOM.progressTrack.getBoundingClientRect();
  const pos = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
  DOM.videoElement.currentTime = pos * (DOM.videoElement.duration || 0);
}

function handleProgressHover(e) {
  const rect = DOM.progressTrack.getBoundingClientRect();
  const pos = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
  const time = pos * (DOM.videoElement.duration || 0);
  DOM.progressHoverTime.textContent = formatTime(time);
  DOM.progressHoverTime.style.left = `${pos * 100}%`;
  DOM.progressHoverTime.style.display = 'block';
}

function updateVideoProgress() {
  const current = DOM.videoElement.currentTime || 0;
  const duration = DOM.videoElement.duration || 0;

  DOM.currentTime.textContent = formatTime(current);
  DOM.totalDuration.textContent = formatTime(duration);

  if (duration > 0) {
    const percent = (current / duration) * 100;
    DOM.progressFilled.style.width = `${percent}%`;
    const thumb = document.querySelector('.player-progress-thumb');
    if (thumb) thumb.style.left = `${percent}%`;
  }

  if (DOM.videoElement.buffered.length > 0 && duration > 0) {
    const bufferedEnd = DOM.videoElement.buffered.end(DOM.videoElement.buffered.length - 1);
    DOM.progressBuffered.style.width = `${(bufferedEnd / duration) * 100}%`;
  }

  if (Math.floor(current) % 5 === 0) {
    saveCurrentProgress();
  }
}

function saveCurrentProgress() {
  if (!state.currentDetails || !DOM.videoElement.duration) return;
  const current = DOM.videoElement.currentTime;
  const duration = DOM.videoElement.duration;
  if (current < 10) return;

  const item = {
    id: state.currentDetails.id,
    title: state.currentDetails.title,
    poster_url: state.currentDetails.poster_url,
    is_series: state.currentDetails.is_series,
    season: state.selectedSeason,
    episode: state.selectedEpisode,
    currentTime: current,
    duration: duration,
    timestamp: Date.now()
  };

  state.watchHistory = state.watchHistory.filter(h =>
    !(h.id === item.id && (!h.is_series || (h.season === item.season && h.episode === item.episode)))
  );
  state.watchHistory.unshift(item);
  if (state.watchHistory.length > 25) state.watchHistory.pop();
  localStorage.setItem('movietap_history', JSON.stringify(state.watchHistory));
}

function handleVideoEnded() {
  saveCurrentProgress();
  if (state.currentDetails && state.currentDetails.is_series) {
    playNextEpisode();
  }
}

function playNextEpisode() {
  if (!state.currentDetails || !state.currentDetails.is_series) return;
  const nextEp = state.selectedEpisode + 1;
  state.selectedEpisode = nextEp;
  showToast(`Playing Episode ${nextEp}...`);
  startPlayback(state.currentDetails, state.activeDub, state.selectedSeason, nextEp);
}

function toggleMute() {
  DOM.videoElement.muted = !DOM.videoElement.muted;
  updateVolumeIcon();
}

function updateVolumeIcon() {
  if (DOM.videoElement.muted || DOM.videoElement.volume === 0) {
    DOM.btnVolume.innerHTML = '<i class="fa-solid fa-volume-xmark"></i>';
  } else if (DOM.videoElement.volume < 0.5) {
    DOM.btnVolume.innerHTML = '<i class="fa-solid fa-volume-low"></i>';
  } else {
    DOM.btnVolume.innerHTML = '<i class="fa-solid fa-volume-high"></i>';
  }
}

function togglePictureInPicture() {
  if (document.pictureInPictureElement) {
    document.exitPictureInPicture();
  } else if (document.pictureInPictureEnabled && DOM.videoElement) {
    DOM.videoElement.requestPictureInPicture();
  }
}

function toggleFullscreen() {
  if (!document.fullscreenElement) {
    DOM.playerContainer.requestFullscreen().catch(err => {
      console.warn("Fullscreen request error:", err);
    });
    DOM.btnFullscreen.innerHTML = '<i class="fa-solid fa-compress"></i>';
  } else {
    document.exitFullscreen();
    DOM.btnFullscreen.innerHTML = '<i class="fa-solid fa-expand"></i>';
  }
}

function resetControlsTimer() {
  DOM.playerContainer.classList.remove('hide-controls');
  clearTimeout(state.controlsTimeout);
  if (state.isPlaying) {
    state.controlsTimeout = setTimeout(() => {
      if (!DOM.audioSubDrawer.classList.contains('active')) {
        DOM.playerContainer.classList.add('hide-controls');
        closeAllDropdowns();
      }
    }, 3500);
  }
}

function toggleDropdown(dropdown) {
  const isOpen = dropdown.classList.contains('active');
  closeAllDropdowns();
  if (!isOpen) dropdown.classList.add('active');
}

function closeAllDropdowns() {
  DOM.qualityMenu.classList.remove('active');
  DOM.speedMenu.classList.remove('active');
}

// ----------------- Keyboard Shortcuts -----------------
function handleKeyboardShortcuts(e) {
  if (document.activeElement === DOM.searchInput) return;

  const isPlayerOpen = DOM.playerModal.classList.contains('active');

  if (e.key === 'Escape') {
    if (DOM.downloadModal.classList.contains('active')) {
      closeDownloadModal();
    } else if (DOM.audioSubDrawer.classList.contains('active')) {
      closeAudioSubDrawer();
    } else if (isPlayerOpen) {
      closePlayer();
    } else if (DOM.detailsModal.classList.contains('active')) {
      closeDetails();
    }
    return;
  }

  if (isPlayerOpen) {
    switch (e.key) {
      case ' ':
      case 'k':
      case 'K':
        e.preventDefault();
        togglePlayPause();
        break;
      case 'ArrowLeft':
        e.preventDefault();
        seekRelative(-10);
        break;
      case 'ArrowRight':
        e.preventDefault();
        seekRelative(10);
        break;
      case 'ArrowUp':
        e.preventDefault();
        DOM.videoElement.volume = Math.min(1, DOM.videoElement.volume + 0.1);
        DOM.volumeSlider.value = DOM.videoElement.volume;
        updateVolumeIcon();
        break;
      case 'ArrowDown':
        e.preventDefault();
        DOM.videoElement.volume = Math.max(0, DOM.videoElement.volume - 0.1);
        DOM.volumeSlider.value = DOM.videoElement.volume;
        updateVolumeIcon();
        break;
      case 'f':
      case 'F':
        e.preventDefault();
        toggleFullscreen();
        break;
      case 'm':
      case 'M':
        e.preventDefault();
        toggleMute();
        break;
      case 'a':
      case 'A':
        e.preventDefault();
        toggleAudioSubDrawer();
        break;
      case 'd':
      case 'D':
        e.preventDefault();
        if (state.currentDetails) openDownloadModal(state.currentDetails, state.activeDub);
        break;
    }
  }
}

// ----------------- Watchlist & Watch History -----------------
function toggleWatchlist(item) {
  const idx = state.watchlist.findIndex(w => w.id === item.id);
  if (idx >= 0) {
    state.watchlist.splice(idx, 1);
    showToast(`Removed "${item.title}" from Watchlist`);
  } else {
    state.watchlist.unshift({
      id: item.id,
      title: item.title,
      poster_url: item.poster_url,
      is_series: item.is_series,
      year: item.year,
      rating: item.rating
    });
    showToast(`Added "${item.title}" to Watchlist`);
  }
  localStorage.setItem('movietap_watchlist', JSON.stringify(state.watchlist));
  updateWatchlistBadge();

  const isSaved = state.watchlist.some(w => w.id === item.id);
  DOM.modalWatchlistBtn.innerHTML = isSaved
    ? '<i class="fa-solid fa-bookmark"></i> In Watchlist'
    : '<i class="fa-regular fa-bookmark"></i> Add to Watchlist';

  if (state.activeTab === 'watchlist') {
    renderWatchlistView();
  }
}

function updateWatchlistBadge() {
  const cnt = state.watchlist.length;
  DOM.watchlistCount.textContent = cnt;
  if (DOM.heroWatchlistCount) DOM.heroWatchlistCount.textContent = cnt;
}

function renderContinueWatching() {
  if (!state.watchHistory || state.watchHistory.length === 0) {
    DOM.continueWatchingSection.style.display = 'none';
    return;
  }

  DOM.continueWatchingSection.style.display = 'block';
  DOM.continueWatchingGrid.innerHTML = state.watchHistory.map(h => {
    const progressPercent = Math.min(100, (h.currentTime / (h.duration || 1)) * 100);
    const subLabel = h.is_series ? `S${h.season} E${h.episode}` : formatTime(h.currentTime);
    return `
      <div class="media-card" data-id="${h.id}" data-season="${h.season || 0}" data-episode="${h.episode || 0}">
        <div class="poster-wrapper">
          <img class="poster-img" src="${h.poster_url || '/static/placeholder.jpg'}" alt="${escapeHtml(h.title)}" onerror="this.src='https://placehold.co/300x450/151a27/9da8b6?text=No+Poster'">
          <div class="card-play-overlay">
            <div class="card-play-btn"><i class="fa-solid fa-play"></i></div>
          </div>
          <div class="card-watch-progress">
            <div class="card-watch-progress-filled" style="width: ${progressPercent}%;"></div>
          </div>
        </div>
        <div class="card-info">
          <h4 class="card-title">${escapeHtml(h.title)}</h4>
          <div class="card-meta">
            <span>${subLabel}</span>
            <span><i class="fa-solid fa-clock"></i> ${formatTime(h.duration - h.currentTime)} left</span>
          </div>
        </div>
      </div>
    `;
  }).join('');

  DOM.continueWatchingGrid.querySelectorAll('.media-card').forEach(card => {
    card.addEventListener('click', () => {
      const id = card.getAttribute('data-id');
      openDetails(id, true);
    });
  });
}

function clearHistory() {
  if (confirm("Clear your watch history?")) {
    state.watchHistory = [];
    localStorage.removeItem('movietap_history');
    localStorage.removeItem('moviebox_history');
    renderContinueWatching();
    showToast("Watch history cleared");
  }
}

function clearWatchlist() {
  if (confirm("Clear all items from your watchlist?")) {
    state.watchlist = [];
    localStorage.removeItem('movietap_watchlist');
    localStorage.removeItem('moviebox_watchlist');
    updateWatchlistBadge();
    renderWatchlistView();
    showToast("Watchlist cleared");
  }
}

function renderWatchlistView() {
  if (state.watchlist.length === 0) {
    DOM.watchlistGrid.innerHTML = `
      <div class="empty-state">
        <i class="fa-regular fa-bookmark empty-icon"></i>
        <h3>Your watchlist is empty</h3>
        <p>Save movies and TV series you want to watch later by clicking the bookmark icon.</p>
      </div>
    `;
  } else {
    renderGrid(DOM.watchlistGrid, state.watchlist);
  }
}

// ----------------- Utilities -----------------
function formatTime(seconds) {
  if (isNaN(seconds) || seconds < 0) return '00:00';
  const hrs = Math.floor(seconds / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);
  if (hrs > 0) {
    return `${hrs}:${mins < 10 ? '0' : ''}${mins}:${secs < 10 ? '0' : ''}${secs}`;
  }
  return `${mins < 10 ? '0' : ''}${mins}:${secs < 10 ? '0' : ''}${secs}`;
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

let toastTimer = null;
function showToast(message) {
  DOM.toast.textContent = message;
  DOM.toast.classList.add('active');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    DOM.toast.classList.remove('active');
  }, 3200);
}

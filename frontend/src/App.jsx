import React, { useState, useEffect } from 'react';
import './App.css';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

function App() {
  const [posts, setPosts] = useState([]);
  const [config, setConfig] = useState({
    keywords: 'fidget slider',
    interval_minutes: 60,
    max_products: 10,
    use_fallback: true,
    database_type: 'json'
  });
  const [status, setStatus] = useState({
    scheduler: {
      last_run: 'Never',
      next_run: 'Pending',
      status: 'Offline',
      is_scraping: false,
      last_run_scraped_count: 0,
      last_run_new_posts_count: 0
    },
    database: {
      type: 'json',
      total_posts_saved: 0
    }
  });

  const [activeTab, setActiveTab] = useState('blog'); // 'blog' | 'settings'
  const [theme, setTheme] = useState('dark');
  const [searchQuery, setSearchQuery] = useState('');
  const [isScraping, setIsScraping] = useState(false);
  const [toast, setToast] = useState(null);

  // Form states
  const [formKeywords, setFormKeywords] = useState('');
  const [formInterval, setFormInterval] = useState(60);
  const [formMaxProducts, setFormMaxProducts] = useState(10);
  const [formUseFallback, setFormUseFallback] = useState(true);
  const [formDbType, setFormDbType] = useState('json');

  // Trigger Toast Notification
  const showToast = (message) => {
    setToast(message);
    setTimeout(() => {
      setToast(null);
    }, 4000);
  };

  // Fetch all endpoints
  const fetchPosts = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/posts`);
      if (res.ok) {
        const data = await res.json();
        setPosts(data);
      }
    } catch (err) {
      console.error('Error fetching posts:', err);
    }
  };

  const fetchConfig = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/config`);
      if (res.ok) {
        const data = await res.json();
        setConfig(data);
        // Sync forms
        setFormKeywords(data.keywords);
        setFormInterval(data.interval_minutes);
        setFormMaxProducts(data.max_products);
        setFormUseFallback(data.use_fallback);
        setFormDbType(data.database_type);
      }
    } catch (err) {
      console.error('Error fetching config:', err);
    }
  };

  const fetchStatus = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/status`);
      if (res.ok) {
        const data = await res.json();
        setStatus(data);
        setIsScraping(data.scheduler.is_scraping);
      }
    } catch (err) {
      console.error('Error fetching status:', err);
    }
  };

  const loadAllData = () => {
    fetchPosts();
    fetchConfig();
    fetchStatus();
  };

  // Initial mount
  useEffect(() => {
    loadAllData();
    // Poll status and posts every 10 seconds to show background scraper updates
    const interval = setInterval(() => {
      fetchStatus();
      fetchPosts();
    }, 10000);

    return () => clearInterval(interval);
  }, []);

  // Sync theme
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  // Handle Manual Scrape
  const handleStartScrape = async () => {
    if (isScraping) return;
    setIsScraping(true);
    showToast('Varredura AliExpress iniciada em segundo plano...');
    try {
      const res = await fetch(`${API_BASE}/api/scrape`, { method: 'POST' });
      if (res.ok) {
        showToast('Comando enviado! Aguardando retorno do robô.');
        // Brief delay to let the scraper progress
        setTimeout(() => {
          loadAllData();
        }, 3000);
      } else {
        const errData = await res.json();
        showToast(`Erro: ${errData.detail || 'Falha no Scraper'}`);
        setIsScraping(false);
      }
    } catch (err) {
      showToast('Erro de rede ao disparar scraper.');
      setIsScraping(false);
    }
  };

  // Handle Save Settings
  const handleSaveSettings = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch(`${API_BASE}/api/config`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          keywords: formKeywords,
          interval_minutes: parseInt(formInterval),
          max_products: parseInt(formMaxProducts),
          use_fallback: formUseFallback,
          database_type: formDbType
        })
      });

      if (res.ok) {
        const data = await res.json();
        setConfig(data.config);
        showToast('Configurações salvas e aplicadas!');
        fetchStatus();
        fetchPosts();
        setActiveTab('blog');
      } else {
        showToast('Falha ao salvar as propriedades.');
      }
    } catch (err) {
      showToast('Erro de conexão ao salvar configurações.');
    }
  };

  // Clear posts database
  const handleClearDatabase = async () => {
    if (window.confirm('Tem certeza que deseja apagar todos os posts salvos?')) {
      try {
        const res = await fetch(`${API_BASE}/api/posts/clear`, { method: 'POST' });
        if (res.ok) {
          showToast('Banco de dados de posts limpo!');
          loadAllData();
        }
      } catch (err) {
        showToast('Erro ao limpar posts.');
      }
    }
  };

  // Helpers
  const getProductImageUrl = (url) => {
    if (!url) return 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=500&auto=format&fit=crop';
    if (url.startsWith('/static/')) {
      return `${API_BASE}${url}`;
    }
    return url;
  };

  const formatDate = (isoString) => {
    if (!isoString || isoString === 'Never' || isoString === 'Starting...') return isoString;
    try {
      const date = new Date(isoString);
      return date.toLocaleDateString('pt-BR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch (e) {
      return isoString;
    }
  };

  // Filter products locally
  const filteredPosts = posts.filter(post => 
    post.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    post.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
    post.keyword.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="app-container">
      {/* Toast */}
      {toast && <div className="toast-msg">{toast}</div>}

      {/* Header */}
      <header className="app-header">
        <div className="brand-section">
          <div className="brand-logo-glow">A</div>
          <div className="brand-title">
            <h1>AliScraper Blog</h1>
            <p>Varredura Automática de Ofertas no AliExpress</p>
          </div>
        </div>

        <div className="nav-actions">
          <div className="nav-tabs">
            <button 
              className={`tab-btn ${activeTab === 'blog' ? 'active' : ''}`}
              onClick={() => setActiveTab('blog')}
            >
              Blog Posts
            </button>
            <button 
              className={`tab-btn ${activeTab === 'settings' ? 'active' : ''}`}
              onClick={() => setActiveTab('settings')}
            >
              Configurações
            </button>
          </div>

          <button 
            className="theme-toggle-btn"
            onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
            title="Alternar Tema"
          >
            {theme === 'dark' ? (
              <svg width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <circle cx="12" cy="12" r="5"></circle>
                <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"></path>
              </svg>
            ) : (
              <svg width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
              </svg>
            )}
          </button>
        </div>
      </header>

      {/* Stats Bar */}
      <section className="status-bar">
        <div className="status-card">
          <div className="status-title">Status do Robô</div>
          <div className="status-value">
            <span className={`pulse-indicator ${isScraping ? 'scraping' : ''}`}></span>
            {isScraping ? 'Buscando...' : 'Aguardando'}
          </div>
          <div className="status-meta">{status.scheduler.status}</div>
        </div>

        <div className="status-card">
          <div className="status-title">Última Varredura</div>
          <div className="status-value" style={{ fontSize: '1.1rem', marginTop: '4px' }}>
            {status.scheduler.last_run === 'Never' ? 'Nunca Executado' : formatDate(status.scheduler.last_run)}
          </div>
          <div className="status-meta">
            Obtidos: {status.scheduler.last_run_scraped_count} ({status.scheduler.last_run_new_posts_count} novos)
          </div>
        </div>

        <div className="status-card">
          <div className="status-title">Próxima Execução</div>
          <div className="status-value" style={{ fontSize: '1.1rem', marginTop: '4px' }}>
            {formatDate(status.scheduler.next_run)}
          </div>
          <div className="status-meta">Intervalo: {config.interval_minutes} min</div>
        </div>

        <div className="status-card">
          <div className="status-title">Banco de Dados</div>
          <div className="status-value">
            {status.database.total_posts_saved} <span style={{ fontSize: '0.85rem', fontWeight: 500, color: 'var(--text-secondary)' }}>posts</span>
          </div>
          <div className="status-meta">Tipo: {status.database.type.toUpperCase()}</div>
        </div>
      </section>

      {/* Tab Switcher */}
      {activeTab === 'blog' && (
        <>
          {/* Dashboard Control Banner */}
          <div className="control-banner">
            <div className="search-filter-box">
              <svg className="search-icon" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
                <circle cx="11" cy="11" r="8"></circle>
                <path d="M21 21l-4.35-4.35"></path>
              </svg>
              <input 
                type="text" 
                className="search-input" 
                placeholder="Pesquisar posts por título, descrição ou tag..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>

            <div className="action-buttons">
              <button 
                className="btn btn-primary"
                onClick={handleStartScrape}
                disabled={isScraping}
              >
                {isScraping ? (
                  <>
                    <svg className="spin" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
                      <circle cx="12" cy="12" r="10" strokeDasharray="32" strokeDashoffset="12"></circle>
                    </svg>
                    Varrendo AliExpress...
                  </>
                ) : (
                  <>
                    <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
                      <path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l.73-.73"></path>
                    </svg>
                    Varrer Agora
                  </>
                )}
              </button>

              <button 
                className="btn btn-secondary" 
                onClick={loadAllData}
                title="Recarregar dados da API"
              >
                Atualizar
              </button>
            </div>
          </div>

          {/* Posts list */}
          {filteredPosts.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">🔍</div>
              <h2 className="empty-title">Nenhum post encontrado</h2>
              <p className="empty-desc">
                {searchQuery 
                  ? 'Nenhum resultado corresponde à sua pesquisa. Tente buscar por outros termos.'
                  : 'Nenhum produto foi importado do AliExpress ainda. Verifique se o backend está ligado e clique em "Varrer Agora" para carregar!'
                }
              </p>
              {!searchQuery && (
                <button className="btn btn-primary" onClick={handleStartScrape} disabled={isScraping}>
                  Iniciar Primeira Busca
                </button>
              )}
            </div>
          ) : (
            <main className="posts-grid">
              {filteredPosts.map((post) => (
                <article className="post-card" key={post.product_id}>
                  <div className="card-image-wrapper">
                    <img 
                      src={getProductImageUrl(post.image_url)} 
                      alt={post.title} 
                      className="card-image"
                      onError={(e) => {
                        e.target.onerror = null;
                        e.target.src = 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=500&auto=format&fit=crop';
                      }}
                    />
                    <span className="card-badge">{post.keyword}</span>
                    <span className="card-price-tag">
                      {post.price ? `$${post.price.toFixed(2)}` : 'Preço sob consulta'}
                    </span>
                  </div>

                  <div className="card-content">
                    <div className="card-meta">
                      <div className="card-rating" title={`Nota: ${post.rating}`}>
                        <span>★</span>
                        <span className="card-rating-text">{post.rating.toFixed(1)}</span>
                        <span style={{ color: 'var(--text-muted)' }}>({post.reviews_count} reviews)</span>
                      </div>
                      <span>{formatDate(post.created_at)}</span>
                    </div>

                    <h2 className="card-title">{post.title}</h2>
                    <p className="card-desc">{post.description}</p>

                    <div className="card-footer">
                      <a 
                        href={post.product_url} 
                        target="_blank" 
                        rel="noopener noreferrer" 
                        className="btn btn-primary btn-card"
                      >
                        Comprar no AliExpress
                        <svg width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24" style={{ marginLeft: '4px' }}>
                          <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6M15 3h6v6M10 14L21 3"></path>
                        </svg>
                      </a>
                    </div>
                  </div>
                </article>
              ))}
            </main>
          )}
        </>
      )}

      {activeTab === 'settings' && (
        <section className="settings-container">
          <h2 style={{ marginBottom: '20px', fontWeight: 700 }}>Configurações do Sistema</h2>
          <form onSubmit={handleSaveSettings}>
            <div className="settings-grid">
              <div className="form-group">
                <label className="form-label">Palavras-chave AliExpress</label>
                <input 
                  type="text" 
                  className="form-input" 
                  value={formKeywords}
                  onChange={(e) => setFormKeywords(e.target.value)}
                  required
                />
                <span className="form-desc">
                  Separadas por vírgula. Ex: fidget slider, fidget spinner. Inicialmente: "fidget slider".
                </span>
              </div>

              <div className="form-group">
                <label className="form-label">Intervalo de Varredura (Minutos)</label>
                <input 
                  type="number" 
                  className="form-input" 
                  min="1"
                  value={formInterval}
                  onChange={(e) => setFormInterval(e.target.value)}
                  required
                />
                <span className="form-desc">
                  Tempo de espera do robô antes de realizar a próxima busca no AliExpress.
                </span>
              </div>

              <div className="form-group">
                <label className="form-label">Limite Diário de Posts por Busca</label>
                <input 
                  type="number" 
                  className="form-input" 
                  min="1"
                  max="50"
                  value={formMaxProducts}
                  onChange={(e) => setFormMaxProducts(e.target.value)}
                  required
                />
                <span className="form-desc">
                  Limite de novos posts cadastrados do dia. Configurado para 10.
                </span>
              </div>

              <div className="form-group">
                <label className="form-label">Tipo de Banco de Dados</label>
                <select 
                  className="form-select"
                  value={formDbType}
                  onChange={(e) => setFormDbType(e.target.value)}
                >
                  <option value="json">JSON File Database</option>
                  <option value="sqlite">SQLite Database</option>
                </select>
                <span className="form-desc">
                  Define onde guardar os posts. Modificar este valor reconfigura o driver dinamicamente.
                </span>
              </div>

              <div className="form-group form-checkbox-group">
                <input 
                  type="checkbox" 
                  id="useFallback"
                  className="form-checkbox"
                  checked={formUseFallback}
                  onChange={(e) => setFormUseFallback(e.target.checked)}
                />
                <div>
                  <label htmlFor="useFallback" className="form-label" style={{ cursor: 'pointer' }}>
                    Utilizar Fallback Inteligente (Simulado)
                  </label>
                  <span className="form-desc" style={{ display: 'block', marginTop: '2px' }}>
                    Caso AliExpress bloqueie com CAPTCHA ou anti-robô, gera produtos fidget realistas para manter a interface funcionando.
                  </span>
                </div>
              </div>
            </div>

            <div className="settings-actions">
              <button 
                type="button" 
                className="btn btn-danger" 
                style={{ marginRight: 'auto' }}
                onClick={handleClearDatabase}
              >
                Limpar Todos os Posts
              </button>

              <button 
                type="button" 
                className="btn btn-secondary"
                onClick={() => {
                  setActiveTab('blog');
                  // Reset form states to config
                  setFormKeywords(config.keywords);
                  setFormInterval(config.interval_minutes);
                  setFormMaxProducts(config.max_products);
                  setFormUseFallback(config.use_fallback);
                  setFormDbType(config.database_type);
                }}
              >
                Cancelar
              </button>

              <button type="submit" className="btn btn-primary">
                Salvar Propriedades
              </button>
            </div>
          </form>
        </section>
      )}
    </div>
  );
}

export default App;

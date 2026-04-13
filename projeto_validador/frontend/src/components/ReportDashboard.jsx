import { useState, useRef, useEffect } from 'react';
import {
  AlertTriangle, ArrowLeft, Clock, Bot, Layout, List, Download,
  ShieldCheck, RotateCcw, Printer, ChevronDown, FileText, Table2,
  FileSpreadsheet, AlignLeft, Users, Wrench, CheckCircle2, XCircle,
  Info, Zap, Eye, EyeOff,
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import PDFInteractiveViewer from './PDFInteractiveViewer';

/* ─── Mapeamento de códigos de erro para linguagem humana ───────────────── */
const ERROR_DESCRIPTIONS = {
  // Cores
  color_mode:         { client: 'Modo de cor incorreto',        action: 'O arquivo deve estar em CMYK, não RGB. Reconverta no Photoshop/Illustrator.' },
  icc_profile:        { client: 'Perfil de cor ausente',         action: 'Incorpore um perfil ICC ao salvar o PDF (ex: ISO Coated v2).' },
  rich_black:         { client: 'Preto composto demais',         action: 'Textos pequenos devem usar preto puro (K=100). Ajuste as camadas de cor.' },
  overprint:          { client: 'Sobreimpressão inadequada',     action: 'Verifique configurações de sobreimpressão no Illustrator/InDesign.' },
  // Fontes
  font_embedded:      { client: 'Fontes não incorporadas',       action: 'Ao exportar o PDF, ative "Incorporar todas as fontes".' },
  font_subset:        { client: 'Fontes não subconjuntadas',     action: 'Ative "Subconjunto de fontes" ao exportar o PDF.' },
  // Imagens
  image_resolution:   { client: 'Resolução de imagem baixa',    action: 'Use imagens com mínimo de 300 DPI para impressão de qualidade.' },
  compression:        { client: 'Compressão excessiva',          action: 'Salve com qualidade de imagem alta (mínimo 80%).' },
  // Estrutura
  bleed:              { client: 'Sangria insuficiente',          action: 'Adicione 3mm de sangria em todos os lados do arquivo.' },
  trim_box:           { client: 'Área de corte não definida',    action: 'Defina a TrimBox corretamente ao exportar o PDF.' },
  page_size:          { client: 'Tamanho de página incorreto',   action: 'Verifique as dimensões do documento e ajuste para o formato contratado.' },
  // Transparência
  transparency:       { client: 'Transparências não achatadas',  action: 'Achate as transparências antes de exportar (Efeitos > Achatar Transparência).' },
  // DeviceN / Especial
  spot_color:         { client: 'Cor especial não esperada',     action: 'Converta todas as cores especiais (Pantone) para CMYK ou remova se não contratadas.' },
  devicen:            { client: 'Canal de cor especial detectado', action: 'Verifique se cores especiais foram contratadas ou remova-as.' },
};

const getErrorMeta = (code, label) => {
  const key = Object.keys(ERROR_DESCRIPTIONS).find(k => code?.toLowerCase().includes(k) || label?.toLowerCase().includes(k));
  return key ? ERROR_DESCRIPTIONS[key] : {
    client: label,
    action: 'Consulte seu designer ou equipe de pré-impressão para corrigir este item.',
  };
};

/* ─── Score Ring ─────────────────────────────────────────────────────────── */
const ScoreRing = ({ score, color, size = 100 }) => {
  const sw = 5, r = (size - sw * 2) / 2;
  const circ = 2 * Math.PI * r;
  return (
    <div style={{ width: size, height: size, position: 'relative' }}>
      <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
        <circle cx={size/2} cy={size/2} r={r} stroke="rgba(255,255,255,0.05)" strokeWidth={sw} fill="none"/>
        <circle cx={size/2} cy={size/2} r={r} stroke={color} strokeWidth={sw} fill="none"
          strokeDasharray={circ} strokeDashoffset={circ - (score/100)*circ}
          strokeLinecap="round" style={{ transition: 'stroke-dashoffset 1s ease' }}/>
      </svg>
      <div style={{ position:'absolute',inset:0,display:'flex',alignItems:'center',justifyContent:'center',flexDirection:'row',gap:1 }}>
        <span style={{ fontSize:28,fontWeight:700,color:'white',fontFamily:'Outfit' }}>{score}</span>
        <span style={{ fontSize:13,color:'#64748b',marginTop:6 }}>%</span>
      </div>
    </div>
  );
};

/* ─── Badge de status ────────────────────────────────────────────────────── */
const StatusIcon = ({ status }) => {
  if (status === 'ERRO')  return <XCircle     size={16} color="#ef4444"/>;
  if (status === 'AVISO') return <AlertTriangle size={14} color="#f59e0b"/>;
  return                          <CheckCircle2 size={16} color="#10b981"/>;
};

/* ═══════════════════════════════════════════════════════════════════════════
   REPORT DASHBOARD
   ═══════════════════════════════════════════════════════════════════════════ */
const ReportDashboard = ({ report, onReset }) => {
  const [filterSeverity, setFilterSeverity] = useState('ALL');
  const [activeLayout, setActiveLayout]     = useState('split');
  const [viewMode, setViewMode]             = useState('tech'); // 'client' | 'tech'
  const [selectedErrorId, setSelectedErrorId] = useState(null);
  const [pageJump, setPageJump]             = useState({ page:1, nonce:0 });
  const [exportMenuOpen, setExportMenuOpen] = useState(false);
  const exportMenuRef = useRef(null);

  useEffect(() => {
    const h = (e) => { if (exportMenuRef.current && !exportMenuRef.current.contains(e.target)) setExportMenuOpen(false); };
    document.addEventListener('mousedown', h);
    return () => document.removeEventListener('mousedown', h);
  }, []);

  /* ─── Data extraction ──────────────────────────────────────────────────── */
  const {
    job_id, status = 'DESCONHECIDO', agente_processador = 'N/A',
    produto = 'N/A', tempo_processamento_ms = 0,
    detalhes_tecnicos = {}, resumo = ''
  } = report;

  const validationItems = Object.entries(detalhes_tecnicos)
    .filter(([, val]) => val && typeof val === 'object' && 'status' in val)
    .map(([key, val]) => ({
      id: key,
      label: val.label || key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
      status: val.status || 'OK',
      code: val.error_code || val.codigo || key,
      value: val.found_value || val.value_found || val.valor || '',
      expected: val.expected_value || val.value_expected || '',
      pages: Array.isArray(val.paginas) ? val.paginas : [],
      meta: getErrorMeta(val.error_code || val.codigo || key, val.label || key.replace(/_/g,' ')),
    }));

  const totalChecks  = validationItems.length || 1;
  const errorCount   = validationItems.filter(v => v.status === 'ERRO').length;
  const warningCount = validationItems.filter(v => v.status === 'AVISO').length;
  const okCount      = totalChecks - errorCount - warningCount;
  const score        = Math.max(0, Math.round(((totalChecks - errorCount - warningCount * 0.4) / totalChecks) * 100));

  const statusConfig = (() => {
    switch(status) {
      case 'APROVADO':              return { color:'#10b981', label:'Pronto para Impressão',  icon: ShieldCheck };
      case 'APROVADO_COM_RESSALVAS':return { color:'#f59e0b', label:'Aprovado com Ressalvas', icon: AlertTriangle };
      default:                      return { color:'#ef4444', label:'Reprovado',              icon: AlertTriangle };
    }
  })();

  const filteredItems = validationItems.filter(i => filterSeverity === 'ALL' || i.status === filterSeverity);
  const fileUrl = `${window.location.origin}/api/v1/jobs/${job_id}/file`;
  const shortId = typeof job_id === 'string' ? job_id.slice(0, 8) : '—';
  const dateStr = new Date().toLocaleDateString('pt-BR');

  /* ─── Export utilities ─────────────────────────────────────────────────── */
  const triggerDownload = (content, filename, mimeType) => {
    // Sanitização extrema para evitar bloqueios do sistema operacional
    const safeName = filename.replace(/[/\\?%*:|"<>]/g, '-');
    const blob = new Blob([content], { type: mimeType });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    
    a.href = url;
    a.download = safeName;
    a.style.display = 'none';
    document.body.appendChild(a);
    a.click();

    // Mantemos a URL ativa por 10 segundos para garantir que o Chrome termine a escrita em disco
    setTimeout(() => {
      if (document.body.contains(a)) document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }, 10000);
  };

  /* PDF — documento HTML estilizado em nova janela → print */
  const handleExportPDF = () => {
    setExportMenuOpen(false);

    const statusColor = statusConfig.color;
    const errItems    = validationItems.filter(v => v.status === 'ERRO');
    const warnItems   = validationItems.filter(v => v.status === 'AVISO');
    const okItems     = validationItems.filter(v => v.status === 'OK');

    const rowsHTML = (items, color) => items.map(i => `
      <tr>
        <td style="border-left:3px solid ${color};padding-left:10px">${i.label}</td>
        <td><code style="font-size:11px;color:#555">${i.code}</code></td>
        <td style="font-weight:700">${i.value || '—'}</td>
        <td style="color:#64748b">${i.expected || '—'}</td>
        <td>${i.pages.length ? i.pages.map(p=>`Pág ${p}`).join(', ') : '—'}</td>
        <td style="font-size:11px;color:#555">${i.meta.action}</td>
      </tr>`).join('');

    const html = `<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8"/>
<title>Relatório Preflight — ${produto}</title>
<style>
  *{margin:0;padding:0;box-sizing:border-box}
  body{font-family:'Segoe UI',Arial,sans-serif;color:#1e293b;background:#fff;font-size:13px}
  .page{max-width:900px;margin:0 auto;padding:40px 48px}
  .cover{display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:36px;padding-bottom:24px;border-bottom:2px solid #e2e8f0}
  .brand{font-size:11px;font-weight:700;color:#94a3b8;letter-spacing:2px;text-transform:uppercase;margin-bottom:8px}
  h1{font-size:24px;font-weight:800;color:#0f172a;margin-bottom:4px}
  .meta{font-size:11px;color:#94a3b8}
  .badge{padding:8px 18px;border-radius:8px;font-weight:800;font-size:14px;color:white;background:${statusColor}}
  .scoreblock{text-align:right}
  .scorenum{font-size:48px;font-weight:900;color:${statusColor};line-height:1}
  .scorelabel{font-size:11px;color:#94a3b8;font-weight:600;letter-spacing:1px}
  .summary-box{background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;padding:20px 24px;margin-bottom:28px}
  .summary-box h2{font-size:14px;font-weight:700;color:#0f172a;margin-bottom:8px}
  .summary-box p{color:#475569;line-height:1.7}
  .kpis{display:flex;gap:16px;margin-bottom:28px}
  .kpi{flex:1;padding:16px;border-radius:10px;border:1px solid #e2e8f0;text-align:center}
  .kpi-num{font-size:28px;font-weight:800}
  .kpi-label{font-size:11px;color:#94a3b8;font-weight:600;margin-top:4px}
  .kpi.err .kpi-num{color:#ef4444} .kpi.warn .kpi-num{color:#f59e0b} .kpi.ok .kpi-num{color:#10b981}
  h2.section{font-size:16px;font-weight:700;border-bottom:1px solid #e2e8f0;padding-bottom:8px;margin:24px 0 14px}
  table{width:100%;border-collapse:collapse;font-size:12px}
  th{background:#f1f5f9;padding:8px 10px;text-align:left;font-weight:700;color:#475569;font-size:11px;text-transform:uppercase;letter-spacing:.5px}
  td{padding:9px 10px;border-bottom:1px solid #f1f5f9;vertical-align:top}
  tr:hover td{background:#fafafa}
  .client-card{background:#fff7ed;border:1px solid #fed7aa;border-radius:10px;padding:14px 18px;margin-bottom:10px}
  .client-card.erro{background:#fef2f2;border-color:#fecaca}
  .client-card.aviso{background:#fffbeb;border-color:#fed7aa}
  .client-title{font-weight:700;color:#1e293b;margin-bottom:4px;font-size:13px}
  .client-action{color:#475569;font-size:12px}
  .client-action strong{color:#0f172a}
  .footer{margin-top:40px;padding-top:16px;border-top:1px solid #e2e8f0;display:flex;justify-content:space-between;font-size:10px;color:#94a3b8}
  @media print{@page{margin:20mm}}
</style>
</head>
<body>
<div class="page">
  <div class="cover">
    <div>
      <div class="brand">PreFlight Inspector · Relatório de Validação</div>
      <h1>${produto}</h1>
      <p class="meta">Job: ${job_id} &nbsp;·&nbsp; ${dateStr} &nbsp;·&nbsp; Agente: ${agente_processador} &nbsp;·&nbsp; ${tempo_processamento_ms}ms</p>
      <br/>
      <span class="badge">${statusConfig.label.toUpperCase()}</span>
    </div>
    <div class="scoreblock">
      <div class="scorenum">${score}<span style="font-size:24px">%</span></div>
      <div class="scorelabel">SCORE DE QUALIDADE</div>
    </div>
  </div>

  <div class="summary-box">
    <h2>Resumo Executivo</h2>
    <p>${resumo || 'Arquivo processado pelo sistema de validação preflight GWG 2022.'}</p>
  </div>

  <div class="kpis">
    <div class="kpi err"><div class="kpi-num">${errorCount}</div><div class="kpi-label">Erros Críticos</div></div>
    <div class="kpi warn"><div class="kpi-num">${warningCount}</div><div class="kpi-label">Avisos</div></div>
    <div class="kpi ok"><div class="kpi-num">${okCount}</div><div class="kpi-label">Checks OK</div></div>
    <div class="kpi"><div class="kpi-num">${totalChecks}</div><div class="kpi-label">Total Verificado</div></div>
  </div>

  ${errItems.length ? `
  <h2 class="section" style="color:#ef4444">⛔ Erros que impedem a impressão (${errItems.length})</h2>
  ${errItems.map(i => `
  <div class="client-card erro">
    <div class="client-title">${i.meta.client}</div>
    <div class="client-action"><strong>O que fazer:</strong> ${i.meta.action}${i.pages.length ? ` <em>(Páginas: ${i.pages.join(', ')})</em>` : ''}</div>
  </div>`).join('')}` : ''}

  ${warnItems.length ? `
  <h2 class="section" style="color:#f59e0b">⚠️ Avisos (${warnItems.length})</h2>
  ${warnItems.map(i => `
  <div class="client-card aviso">
    <div class="client-title">${i.meta.client}</div>
    <div class="client-action"><strong>O que verificar:</strong> ${i.meta.action}${i.pages.length ? ` <em>(Páginas: ${i.pages.join(', ')})</em>` : ''}</div>
  </div>`).join('')}` : ''}

  <h2 class="section">Tabela Técnica Completa</h2>
  <table>
    <thead><tr><th>Check</th><th>Código</th><th>Encontrado</th><th>Esperado</th><th>Páginas</th><th>Ação Recomendada</th></tr></thead>
    <tbody>
      ${rowsHTML(errItems, '#ef4444')}
      ${rowsHTML(warnItems, '#f59e0b')}
      ${rowsHTML(okItems, '#10b981')}
    </tbody>
  </table>

  <div class="footer">
    <span>PreFlight Inspector · GWG 2022 Compliance</span>
    <span>Gerado em ${new Date().toLocaleString('pt-BR')}</span>
  </div>
</div>
<script>window.onload=()=>window.print()</script>
</body></html>`;

    const w = window.open('', '_blank');
    w.document.write(html);
    w.document.close();
  };

  /* CSV — cabeçalho rico + dados */
  const handleExportCSV = () => {
    setExportMenuOpen(false);
    const esc  = (v) => `"${String(v ?? '').replace(/"/g,'""')}"`;
    const hdr  = ['Código','Check','Status','Descrição para Cliente','Ação Recomendada','Encontrado','Esperado','Páginas'];
    const rows = validationItems.map(i => [
      i.code, i.label, i.status, i.meta.client, i.meta.action,
      i.value, i.expected, i.pages.join('; ')
    ]);
    const meta = [
      `# RELATÓRIO DE VALIDAÇÃO PREFLIGHT`,
      `# Job: ${job_id}`,
      `# Produto: ${produto}`,
      `# Status: ${status} | Score: ${score}%`,
      `# Erros: ${errorCount} | Avisos: ${warningCount} | OK: ${okCount}`,
      `# Agente: ${agente_processador} | Tempo: ${tempo_processamento_ms}ms`,
      `# Gerado: ${new Date().toLocaleString('pt-BR')}`,
      `# Resumo: ${resumo}`,
      '',
      hdr.map(esc).join(','),
      ...rows.map(r => r.map(esc).join(',')),
    ].join('\n');
    triggerDownload(meta, `Preflight_${shortId}_${dateStr.replace(/\//g,'-')}.csv`, 'text/csv;charset=utf-8;');
  };

  /* Excel — SpreadsheetML puro (sem biblioteca), Excel/LibreOffice abrem nativamente */
  const handleExportXLSX = () => {
    setExportMenuOpen(false);

    const x = (v) => String(v ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
    const cell = (v, bold = false, bg = '') => {
      const style = (bold || bg)
        ? ` ss:StyleID="${bold && bg ? 'hdr' : bold ? 'bold' : 'bg' + bg}"`
        : '';
      return `<Cell${style}><Data ss:Type="String">${x(v)}</Data></Cell>`;
    };
    const row  = (...cells) => `<Row>${cells.join('')}</Row>`;
    const num  = (v)   => `<Cell><Data ss:Type="Number">${v}</Data></Cell>`;
    const empty = (n=1) => `<Cell ss:MergeAcross="${n-1}"/>`;

    const sorted = [
      ...validationItems.filter(i => i.status === 'ERRO'),
      ...validationItems.filter(i => i.status === 'AVISO'),
      ...validationItems.filter(i => i.status === 'OK'),
    ];

    const detailRows = sorted.map(i => row(
      cell(i.status, false, i.status === 'ERRO' ? 'err' : i.status === 'AVISO' ? 'warn' : 'ok'),
      cell(i.code), cell(i.label), cell(i.meta.client), cell(i.meta.action),
      cell(i.value), cell(i.expected), cell(i.pages.join(', '))
    )).join('\n');

    const xml = `<?xml version="1.0" encoding="UTF-8"?>
<?mso-application progid="Excel.Sheet"?>
<Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet"
  xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet">
<Styles>
  <Style ss:ID="bold"><Font ss:Bold="1"/></Style>
  <Style ss:ID="hdr"><Font ss:Bold="1" ss:Color="#FFFFFF"/><Interior ss:Color="#1e293b" ss:Pattern="Solid"/></Style>
  <Style ss:ID="bgerr"><Interior ss:Color="#FEE2E2" ss:Pattern="Solid"/></Style>
  <Style ss:ID="bgwarn"><Interior ss:Color="#FEF9C3" ss:Pattern="Solid"/></Style>
  <Style ss:ID="bgok"><Interior ss:Color="#DCFCE7" ss:Pattern="Solid"/></Style>
  <Style ss:ID="title"><Font ss:Bold="1" ss:Size="14" ss:Color="#0f172a"/></Style>
</Styles>

<Worksheet ss:Name="Resumo">
<Table>
  ${row(`<Cell ss:StyleID="title"><Data ss:Type="String">RELATÓRIO DE VALIDAÇÃO PREFLIGHT</Data></Cell>`)}
  <Row/>
  ${row(cell('Job ID',true),       cell(job_id))}
  ${row(cell('Produto',true),      cell(produto))}
  ${row(cell('Status',true),       cell(status))}
  ${row(cell('Score',true),        cell(score + '%'))}
  ${row(cell('Erros críticos',true), num(errorCount))}
  ${row(cell('Avisos',true),       num(warningCount))}
  ${row(cell('Checks OK',true),    num(okCount))}
  ${row(cell('Total checks',true), num(totalChecks))}
  ${row(cell('Agente',true),       cell(agente_processador))}
  ${row(cell('Tempo (ms)',true),   num(tempo_processamento_ms))}
  ${row(cell('Data',true),         cell(new Date().toLocaleString('pt-BR')))}
  <Row/>
  ${row(cell('Resumo',true),       cell(resumo))}
</Table>
</Worksheet>

<Worksheet ss:Name="Validações">
<Table>
  ${row(
    cell('Status',true,''),cell('Código',true,''),cell('Check Técnico',true,''),
    cell('Descrição (Cliente)',true,''),cell('Ação Recomendada',true,''),
    cell('Encontrado',true,''),cell('Esperado',true,''),cell('Páginas',true,'')
  )}
  ${detailRows}
</Table>
</Worksheet>
</Workbook>`;

    triggerDownload(xml, `Preflight_${shortId}_${dateStr.replace(/\//g,'-')}.xls`, 'application/vnd.ms-excel;charset=utf-8;');
  };

  /* TXT — colunar separado por || */
  const handleExportTXT = () => {
    setExportMenuOpen(false);
    const cols = [
      { key:'status',   label:'STATUS',      w:8  },
      { key:'code',     label:'CÓDIGO',      w:22 },
      { key:'label',    label:'CHECK',       w:28 },
      { key:'client',   label:'DESCRIÇÃO',   w:32 },
      { key:'value',    label:'ENCONTRADO',  w:20 },
      { key:'expected', label:'ESPERADO',    w:20 },
      { key:'pages',    label:'PÁGINAS',     w:14 },
    ];
    const pad = (s, w) => String(s ?? '').padEnd(w).slice(0, w);
    const SEP = ' || ';
    const div = cols.map(c => '-'.repeat(c.w)).join('-++-');
    const hdr = cols.map(c => pad(c.label, c.w)).join(SEP);
    const lineW = hdr.length;

    const sorted = [
      ...validationItems.filter(i => i.status === 'ERRO'),
      ...validationItems.filter(i => i.status === 'AVISO'),
      ...validationItems.filter(i => i.status === 'OK'),
    ];

    const dataRows = sorted.map(i => cols.map(c => {
      if (c.key === 'pages')    return pad(i.pages.join(', '), c.w);
      if (c.key === 'client')   return pad(i.meta.client, c.w);
      return pad(i[c.key], c.w);
    }).join(SEP));

    const errSection = validationItems.filter(i => i.status === 'ERRO').length
      ? [
          '', '== ERROS CRÍTICOS — IMPEDEM IMPRESSÃO ==',
          ...validationItems.filter(i => i.status === 'ERRO').map(i =>
            `  [ERRO] ${i.meta.client}\n         > ${i.meta.action}${i.pages.length ? `  (Págs: ${i.pages.join(', ')})` : ''}`
          ),
        ] : [];

    const warnSection = validationItems.filter(i => i.status === 'AVISO').length
      ? [
          '', '== AVISOS ==',
          ...validationItems.filter(i => i.status === 'AVISO').map(i =>
            `  [AVISO] ${i.meta.client}\n          > ${i.meta.action}`
          ),
        ] : [];

    const content = [
      'RELATÓRIO DE VALIDAÇÃO PREFLIGHT',
      '='.repeat(lineW),
      `Produto : ${produto}`,
      `Job ID  : ${job_id}`,
      `Status  : ${status}`,
      `Score   : ${score}%`,
      `Erros   : ${errorCount}  |  Avisos: ${warningCount}  |  OK: ${okCount}`,
      `Agente  : ${agente_processador}  |  Tempo: ${tempo_processamento_ms}ms`,
      `Data    : ${new Date().toLocaleString('pt-BR')}`,
      `Resumo  : ${resumo}`,
      '='.repeat(lineW),
      ...errSection,
      ...warnSection,
      '',
      '== TABELA TÉCNICA COMPLETA ==',
      hdr, div,
      ...dataRows,
      '',
      `Total: ${totalChecks} checks  ||  Erros: ${errorCount}  ||  Avisos: ${warningCount}  ||  OK: ${okCount}`,
      '='.repeat(lineW),
    ].join('\n');

    triggerDownload(content, `Preflight_${shortId}_${dateStr.replace(/\//g,'-')}.txt`, 'text/plain;charset=utf-8;');
  };

  /* JSON — dados brutos do report */
  const handleExportJSON = () => {
    setExportMenuOpen(false);
    const content = JSON.stringify(report, null, 2);
    triggerDownload(content, `Preflight_${shortId}_${dateStr.replace(/\//g,'-')}.json`, 'application/json;charset=utf-8;');
  };

  /* ═══════════════════════════════════════════════════════════════════════
     RENDER
     ═══════════════════════════════════════════════════════════════════════ */
  return (
    <div className="pf-dash">

      {/* ─── Header ──────────────────────────────────────────────────────── */}
      <header className="pf-header glass-panel">
        <div className="pf-header-left">
          <button className="btn-back" onClick={onReset}><ArrowLeft size={18}/></button>
          <div className="job-info">
            <h1>{produto}</h1>
            <div className="job-meta">
              <span className="id-tag">ID: {shortId}</span>
              <span className="dot"/>
              <span className="agent-tag"><Bot size={12}/> {agente_processador}</span>
              <span className="dot"/>
              <span className="time-tag"><Clock size={12}/> {tempo_processamento_ms}ms</span>
            </div>
          </div>
        </div>

        <div className="pf-header-right">
          {/* Export dropdown */}
          <div className="export-wrap" ref={exportMenuRef}>
            <motion.button
              whileHover={{ scale:1.02 }} whileTap={{ scale:0.98 }}
              className={`btn btn-outline export-trigger ${exportMenuOpen?'active':''}`}
              onClick={() => setExportMenuOpen(o=>!o)}
            >
              <Download size={16}/> Exportar
              <ChevronDown size={13} className={`export-chevron ${exportMenuOpen?'open':''}`}/>
            </motion.button>

            <AnimatePresence>
              {exportMenuOpen && (
                <motion.div
                  initial={{ opacity:0, y:-8, scale:0.97 }}
                  animate={{ opacity:1, y:0, scale:1 }}
                  exit={{ opacity:0, y:-8, scale:0.97 }}
                  transition={{ duration:0.15 }}
                  className="export-dropdown"
                >
                  <button className="export-option" onClick={handleExportPDF}>
                    <span className="export-icon pdf"><FileText size={15}/></span>
                    <span className="export-name">PDF (Relatório)</span>
                  </button>
                  <button className="export-option" onClick={handleExportCSV}>
                    <span className="export-icon csv"><Table2 size={15}/></span>
                    <span className="export-name">CSV (Planilha)</span>
                  </button>
                  <button className="export-option" onClick={handleExportJSON}>
                    <span className="export-icon json"><Bot size={15}/></span>
                    <span className="export-name">JSON (API Debug)</span>
                  </button>
                  <div className="export-divider"/>
                  <button className="export-option" onClick={handleExportXLSX}>
                    <span className="export-icon xlsx"><FileSpreadsheet size={15}/></span>
                    <span className="export-name">Excel (.xlsx)</span>
                  </button>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          <motion.button whileHover={{scale:1.02}} whileTap={{scale:0.98}}
            className="btn btn-primary" onClick={()=>window.print()}>
            <Printer size={16}/> Imprimir
          </motion.button>
        </div>
      </header>

      {/* ─── Body ────────────────────────────────────────────────────────── */}
      <main className={`pf-content ${activeLayout} ${viewMode}`}>

        {/* ─── Painel diagnóstico (esquerda) ──────────────────────────── */}
        <section className="diagnostics-panel">

          {/* Score + status */}
          <div className="health-summary glass-panel">
            <ScoreRing score={score} color={statusConfig.color}/>
            <div className="health-text">
              <h3 style={{ color: statusConfig.color }}>{statusConfig.label}</h3>
              <p>{resumo}</p>
              <div className="kpi-row">
                <span className="kpi-chip err"><XCircle size={12}/> {errorCount} erros</span>
                <span className="kpi-chip warn"><AlertTriangle size={12}/> {warningCount} avisos</span>
                <span className="kpi-chip ok"><CheckCircle2 size={12}/> {okCount} OK</span>
              </div>
            </div>
          </div>

          {/* ── VISTA CLIENTE ────────────────────────────────────────────── */}
          {viewMode === 'client' && (
            <div className="client-view">
              {errorCount > 0 && (
                <div className="client-section err">
                  <h4><XCircle size={16}/> {errorCount} problema{errorCount>1?'s':''} que impedem a impressão</h4>
                  <p className="client-intro">
                    Estes itens precisam ser corrigidos <strong>antes</strong> de enviar para produção.
                  </p>
                  {validationItems.filter(i=>i.status==='ERRO').map(i => (
                    <motion.div key={i.id} className="client-card err"
                      initial={{opacity:0,y:8}} animate={{opacity:1,y:0}}>
                      <div className="client-card-header">
                        <XCircle size={15} color="#ef4444"/>
                        <strong>{i.meta.client}</strong>
                      </div>
                      <p className="client-action"><Zap size={11}/> {i.meta.action}</p>
                      {i.pages.length > 0 && (
                        <div className="client-pages">
                          <Eye size={11}/> Afeta: {i.pages.map(p=><span key={p} className="page-badge">{p}</span>)}
                        </div>
                      )}
                    </motion.div>
                  ))}
                </div>
              )}

              {warningCount > 0 && (
                <div className="client-section warn">
                  <h4><AlertTriangle size={16}/> {warningCount} aviso{warningCount>1?'s':''} — verifique antes de aprovar</h4>
                  {validationItems.filter(i=>i.status==='AVISO').map(i => (
                    <motion.div key={i.id} className="client-card warn"
                      initial={{opacity:0,y:8}} animate={{opacity:1,y:0}}>
                      <div className="client-card-header">
                        <AlertTriangle size={15} color="#f59e0b"/>
                        <strong>{i.meta.client}</strong>
                      </div>
                      <p className="client-action"><Info size={11}/> {i.meta.action}</p>
                      {i.pages.length > 0 && (
                        <div className="client-pages">
                          <Eye size={11}/> Afeta: {i.pages.map(p=><span key={p} className="page-badge">{p}</span>)}
                        </div>
                      )}
                    </motion.div>
                  ))}
                </div>
              )}

              {errorCount === 0 && warningCount === 0 && (
                <div className="client-all-ok">
                  <CheckCircle2 size={40} color="#10b981"/>
                  <h3>Arquivo perfeito!</h3>
                  <p>Todos os {totalChecks} checks passaram. O arquivo está pronto para ir à produção.</p>
                </div>
              )}

              {okCount > 0 && (
                <details className="ok-accordion">
                  <summary>
                    <CheckCircle2 size={13} color="#10b981"/>
                    <span>{okCount} itens aprovados</span>
                    <ChevronDown size={12} className="acc-chevron"/>
                  </summary>
                  <div className="ok-list">
                    {validationItems.filter(i=>i.status==='OK').map(i => (
                      <div key={i.id} className="ok-item">
                        <CheckCircle2 size={12} color="#10b981"/>
                        <span>{i.meta.client}</span>
                      </div>
                    ))}
                  </div>
                </details>
              )}
            </div>
          )}

          {/* ── VISTA TÉCNICO ────────────────────────────────────────────── */}
          {viewMode === 'tech' && (
            <>
              <div className="filters-row">
                <div className="filter-chips">
                  {[['ALL','Tudo',validationItems.length,''],['ERRO','Erros',errorCount,'chip-error'],['AVISO','Avisos',warningCount,'chip-warning'],['OK','OK',okCount,'chip-ok']].map(([val,lbl,cnt,cls])=>(
                    <button key={val} className={`chip ${cls} ${filterSeverity===val?'active':''}`} onClick={()=>setFilterSeverity(val)}>
                      {lbl} <span>{cnt}</span>
                    </button>
                  ))}
                </div>
              </div>

              <div className="results-list">
                <AnimatePresence>
                  {filteredItems.map(item => (
                    <motion.div key={item.id} layout
                      initial={{opacity:0,x:-10}} animate={{opacity:1,x:0}}
                      className={`result-card ${selectedErrorId===item.id?'selected':''} ${item.status}`}
                      onClick={() => {
                        setSelectedErrorId(item.id);
                        const fp = item.pages?.[0];
                        if (fp != null && !Number.isNaN(Number(fp)))
                          setPageJump(j=>({ page:Number(fp), nonce:j.nonce+1 }));
                      }}
                    >
                      <div className="result-header">
                        <div className="result-header-left">
                          <StatusIcon status={item.status}/>
                          <span className="result-label">{item.label}</span>
                        </div>
                        <span className="result-code">{item.code}</span>
                      </div>
                      <p className="result-client-desc">{item.meta.client}</p>
                      {(item.value || item.expected) && (
                        <div className="result-details">
                          <div className="detail"><span>Encontrado:</span> {item.value || '—'}</div>
                          <div className="detail"><span>Esperado:</span>   {item.expected || '—'}</div>
                        </div>
                      )}
                      {item.pages?.length > 0 && (
                        <div className="result-pages">
                          {item.pages.map(p=><span key={p} className="page-tag">Pág {p}</span>)}
                        </div>
                      )}
                    </motion.div>
                  ))}
                </AnimatePresence>
              </div>
            </>
          )}

          {/* Decision footer */}
          <div className="decision-footer glass-panel">
            <h4>Decisão Final</h4>
            <div className="decision-actions">
              <label className="checkbox-container">
                <input type="checkbox"/>
                <span className="checkmark"/>
                Aprovar com ressalvas e assumir responsabilidade
              </label>
              <div className="btn-group">
                <button className="btn btn-outline" style={{flex:1}} onClick={onReset}>
                  <RotateCcw size={16}/> Substituir
                </button>
                <button className="btn btn-primary" style={{flex:1}} disabled={status==='REPROVADO'}>
                  Aprovar para Produção
                </button>
              </div>
            </div>
          </div>
        </section>

        {/* ─── Painel viewer (direita) ─────────────────────────────────── */}
        {activeLayout === 'split' && viewMode === 'tech' && (
          <section className="previewer-panel">
            <PDFInteractiveViewer fileUrl={fileUrl} goToPageRequest={pageJump}/>
          </section>
        )}
      </main>

      <style jsx>{`
        /* ── Layout base ───────────────────────────────────────────────── */
        .pf-dash {
          display: flex; flex-direction: column; height: 100vh;
          max-height: 100vh; gap: 16px; padding: 20px; background: #0a0b10;
        }
        /* ── Header ────────────────────────────────────────────────────── */
        .pf-header {
          display: flex; justify-content: space-between; align-items: center;
          padding: 14px 24px; border-radius: 16px; flex-shrink: 0;
          position: relative; z-index: 100; /* Stacking context for dropdown */
        }
        .pf-header-left  { display:flex; align-items:center; gap:20px; }
        .pf-header-right { display:flex; align-items:center; gap:12px; flex-wrap:wrap; }
        .btn-back {
          background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1);
          color: white; width:40px; height:40px; border-radius:12px;
          cursor:pointer; display:flex; align-items:center; justify-content:center;
        }
        .job-info h1 { font-size:19px; margin-bottom:3px; }
        .job-meta {
          display:flex; align-items:center; gap:10px;
          font-size:11px; color:#64748b; font-weight:600;
        }
        .dot { width:3px; height:3px; background:#334155; border-radius:50%; }

        /* ── View toggle ───────────────────────────────────────────────── */
        .view-toggle {
          display:flex; background:rgba(0,0,0,0.25); padding:3px;
          border-radius:10px; border:1px solid rgba(255,255,255,0.06);
        }
        .view-toggle button {
          display:flex; align-items:center; gap:6px;
          background:transparent; border:none; color:#475569;
          padding:7px 14px; cursor:pointer; border-radius:7px;
          font-size:12px; font-weight:600; transition:all 0.2s;
        }
        .view-toggle button.active { background:#334155; color:white; }

        /* ── Layout picker ─────────────────────────────────────────────── */
        .layout-picker {
          display:flex; background:rgba(0,0,0,0.2);
          padding:4px; border-radius:10px;
        }
        .layout-picker button {
          background:transparent; border:none; color:#475569;
          padding:6px 10px; cursor:pointer; border-radius:6px; transition:all 0.2s;
        }
        .layout-picker button.active { background:#334155; color:white; }

        /* ── Export ────────────────────────────────────────────────────── */
        .export-wrap { position:relative; }
        .export-trigger { display:flex; align-items:center; gap:6px; }
        .export-trigger.active { border-color:rgba(255,255,255,0.25); }
        .export-chevron { transition:transform 0.2s; }
        .export-chevron.open { transform:rotate(180deg); }
        .export-dropdown {
          position: absolute; top: calc(100% + 12px); right: 0; min-width: 280px;
          background: rgba(15, 15, 18, 0.95); /* More opaque for visibility */
          backdrop-filter: blur(24px); -webkit-backdrop-filter: blur(24px);
          border: 1px solid rgba(255, 255, 255, 0.08);
          border-radius: 18px; padding: 10px; z-index: 500; /* Extremely high z-index */
          box-shadow: 0 20px 60px rgba(0, 0, 0, 0.9), 
                      0 0 40px rgba(6, 214, 160, 0.05), /* Subtle accent glow */
                      0 0 0 1px rgba(255, 255, 255, 0.05);
          transform-origin: top right;
        }
        .export-section-label {
          padding:6px 12px 4px; font-size:10px; font-weight:700;
          color:#475569; text-transform:uppercase; letter-spacing:.8px;
        }
        .export-divider { margin:6px 8px; border-top:1px solid rgba(255,255,255,0.06); }
        .export-option {
          display:flex; align-items:center; gap:12px; width:100%;
          padding:10px 12px; background:transparent; border:none;
          border-radius:9px; color:#cbd5e1; cursor:pointer;
          text-align:left; transition:background 0.15s;
        }
        .export-option:hover { 
          background: rgba(255, 255, 255, 0.05); 
          transform: translateX(4px);
        }
        .export-option:active { transform: translateX(2px) scale(0.98); }
        .export-icon {
          width: 34px; height: 34px; border-radius: 10px;
          display: flex; align-items: center; justify-content: center; 
          flex-shrink: 0; transition: transform 0.2s;
        }
        .export-option:hover .export-icon { transform: scale(1.1); }
        .export-icon.pdf  { background:rgba(239,68,68,0.15); color:#ef4444; }
        .export-icon.xlsx { background:rgba(16,185,129,0.15); color:#10b981; }
        .export-icon.csv  { background:rgba(99,102,241,0.15); color:#818cf8; }
        .export-icon.txt  { background:rgba(148,163,184,0.1);  color:#64748b; }
        .export-text { display:flex; flex-direction:column; gap:2px; }
        .export-name { font-size:13px; font-weight:700; }
        .export-hint { font-size:11px; color:#475569; }

        /* ── Content area ──────────────────────────────────────────────── */
        .pf-content {
          display:flex; gap:20px; flex:1; min-height:0;
        }
        .diagnostics-panel {
          flex: 0 0 460px; display:flex; flex-direction:column; gap:14px; min-height:0;
        }
        .pf-content.list .diagnostics-panel,
        .pf-content.client .diagnostics-panel { flex:0 0 100%; max-width:700px; margin:0 auto; }
        .previewer-panel {
          flex:1; border-radius:16px; overflow:hidden; background:#11141d;
        }

        /* ── Health summary ─────────────────────────────────────────────── */
        .health-summary {
          display:flex; align-items:center; gap:20px; padding:20px 24px;
        }
        .health-text h3 { font-size:17px; margin-bottom:4px; }
        .health-text p  { font-size:12px; color:#94a3b8; margin-bottom:10px; line-height:1.5; }
        .kpi-row { display:flex; gap:8px; flex-wrap:wrap; }
        .kpi-chip {
          display:flex; align-items:center; gap:5px;
          padding:3px 10px; border-radius:99px; font-size:11px; font-weight:700;
        }
        .kpi-chip.err  { background:rgba(239,68,68,0.12);  color:#ef4444; }
        .kpi-chip.warn { background:rgba(245,158,11,0.12); color:#f59e0b; }
        .kpi-chip.ok   { background:rgba(16,185,129,0.12); color:#10b981; }

        /* ── Client view ────────────────────────────────────────────────── */
        .client-view { display:flex; flex-direction:column; gap:14px; overflow-y:auto; flex:1; padding-right:4px; }
        .client-section h4 {
          display:flex; align-items:center; gap:8px;
          font-size:14px; font-weight:700; margin-bottom:6px;
        }
        .client-section.err h4 { color:#ef4444; }
        .client-section.warn h4 { color:#f59e0b; }
        .client-intro { font-size:12px; color:#94a3b8; margin-bottom:10px; }
        .client-card {
          border-radius:12px; padding:14px 16px; margin-bottom:8px;
          border:1px solid rgba(255,255,255,0.05);
        }
        .client-card.err  { background:rgba(239,68,68,0.07); border-color:rgba(239,68,68,0.2); }
        .client-card.warn { background:rgba(245,158,11,0.07); border-color:rgba(245,158,11,0.2); }
        .client-card-header { display:flex; align-items:center; gap:8px; margin-bottom:6px; }
        .client-card-header strong { font-size:13px; color:#e2e8f0; }
        .client-action {
          display:flex; align-items:flex-start; gap:6px;
          font-size:12px; color:#94a3b8; line-height:1.5;
        }
        .client-pages {
          display:flex; align-items:center; gap:6px; flex-wrap:wrap;
          margin-top:8px; font-size:11px; color:#64748b;
        }
        .page-badge {
          background:rgba(255,255,255,0.06); color:#94a3b8;
          padding:2px 7px; border-radius:5px; font-size:10px; font-weight:700;
        }
        .client-all-ok {
          display:flex; flex-direction:column; align-items:center; justify-content:center;
          padding:40px 20px; gap:12px; text-align:center; color:#94a3b8;
        }
        .client-all-ok h3 { font-size:20px; color:#10b981; }
        .client-all-ok p  { font-size:13px; }

        /* OK accordion */
        .ok-accordion {
          background:rgba(16,185,129,0.05); border:1px solid rgba(16,185,129,0.15);
          border-radius:12px; overflow:hidden;
        }
        .ok-accordion summary {
          display:flex; align-items:center; gap:8px;
          padding:10px 14px; cursor:pointer; list-style:none;
          font-size:12px; font-weight:600; color:#64748b;
        }
        .ok-accordion summary::-webkit-details-marker { display:none; }
        .acc-chevron { margin-left:auto; transition:transform 0.2s; }
        details[open] .acc-chevron { transform:rotate(180deg); }
        .ok-list { padding:4px 14px 12px; display:flex; flex-direction:column; gap:6px; }
        .ok-item {
          display:flex; align-items:center; gap:8px;
          font-size:12px; color:#64748b;
        }

        /* ── Tech view ─────────────────────────────────────────────────── */
        .filters-row   { display:flex; }
        .filter-chips  { display:flex; gap:8px; flex-wrap:wrap; }
        .chip {
          padding:6px 14px; border-radius:99px;
          border:1px solid rgba(255,255,255,0.05);
          background:rgba(255,255,255,0.03); color:#94a3b8;
          font-size:12px; font-weight:600; cursor:pointer; transition:all 0.2s;
        }
        .chip span { color:#475569; margin-left:6px; }
        .chip.active { background:white; color:black; border-color:white; }
        .chip.active span { color:rgba(0,0,0,0.5); }
        .chip-error.active   { background:#ef4444; color:white; border-color:#ef4444; }
        .chip-warning.active { background:#f59e0b; color:white; border-color:#f59e0b; }
        .chip-ok.active      { background:#10b981; color:white; border-color:#10b981; }

        .results-list {
          flex:1; overflow-y:auto; display:flex; flex-direction:column; gap:10px; padding-right:4px;
        }
        .result-card {
          padding:14px 16px; background:#161922;
          border:1px solid rgba(255,255,255,0.05);
          border-radius:12px; cursor:pointer; transition:all 0.2s;
        }
        .result-card:hover         { border-color:rgba(255,255,255,0.1); transform:translateX(2px); }
        .result-card.selected      { border-color:#3b82f6; background:rgba(59,130,246,0.05); }
        .result-card.ERRO          { border-left:4px solid #ef4444; }
        .result-card.AVISO         { border-left:4px solid #f59e0b; }
        .result-card.OK            { border-left:4px solid #10b981; }

        .result-header       { display:flex; justify-content:space-between; margin-bottom:4px; }
        .result-header-left  { display:flex; align-items:center; gap:8px; }
        .result-label        { font-size:13px; font-weight:600; color:#cbd5e1; }
        .result-code         { font-size:10px; color:#475569; font-family:monospace; }
        .result-client-desc  { font-size:12px; color:#64748b; margin-bottom:8px; }
        .result-details      { font-size:12px; color:#94a3b8; display:grid; gap:4px; }
        .detail span         { color:#475569; font-weight:600; }
        .result-pages        { margin-top:8px; }
        .page-tag {
          display:inline-block; margin-right:4px;
          padding:2px 8px; background:rgba(255,255,255,0.05);
          color:#64748b; font-size:10px; border-radius:4px; font-weight:700;
        }

        /* ── Decision footer ───────────────────────────────────────────── */
        .decision-footer { margin-top:auto; padding:20px 24px; border-radius:16px; }
        .decision-footer h4 { font-size:15px; margin-bottom:14px; }
        .checkbox-container {
          display:flex; align-items:center; gap:12px;
          font-size:12px; color:#94a3b8; cursor:pointer; margin-bottom:16px;
        }
        .btn-group { display:flex; gap:12px; }

        /* ── Print ─────────────────────────────────────────────────────── */
        @media print {
          .btn, .layout-picker, .btn-back, .previewer-panel,
          .decision-footer, .view-toggle, .export-wrap { display:none !important; }
          .pf-dash { background:white !important; color:black !important; padding:0; }
          .glass-panel { background:white !important; border:1px solid #eee !important; box-shadow:none !important; }
          .diagnostics-panel { flex:1 0 100% !important; }
          .result-card { background:white !important; border:1px solid #eee !important; break-inside:avoid; }
        }
      `}</style>
    </div>
  );
};

export default ReportDashboard;

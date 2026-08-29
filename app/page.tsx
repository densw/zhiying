'use client';

import { useMemo, useState } from 'react';
import { Activity, ArrowRight, BarChart3, BookOpenText, BrainCircuit, CheckCircle2, ChevronRight, Database, GitBranch, Orbit, ShieldCheck, Sparkles, Target } from 'lucide-react';

const modules = [
  { url: 'http://analytics.localhost', title: '经营分析中心', eyebrow: '经营洞察', description: '从客户结构、渠道效率到活动转化，统一查看核心经营指标。', tags: ['客户分群', '渠道表现', '转化分析'], icon: BarChart3 },
  { url: 'http://decision.localhost', title: '营销决策中心', eyebrow: '名单优化', description: '根据每日触达容量筛选高潜客户，实时估算转化、成本与收益。', tags: ['优先名单', '增益分析', '收益测算'], icon: Target, featured: true },
  { url: 'http://report.localhost', title: '自动经营报告', eyebrow: '管理简报', description: '把关键变化、成因判断和下一步建议整理成可阅读的经营报告。', tags: ['经营摘要', '归因分析', '行动建议'], icon: BookOpenText },
  { url: 'http://experiments.localhost', title: '模型实验管理', eyebrow: '效果对比', description: '追踪每次训练结果、评估指标与候选版本，保留完整演进记录。', tags: ['版本对比', '指标追踪', '成果归档'], icon: BrainCircuit },
  { url: 'http://monitor.localhost', title: '数据与模型监控', eyebrow: '风险预警', description: '持续观察数据质量、客户分布与预测稳定性，及时发现异常。', tags: ['质量监测', '分布漂移', '表现预警'], icon: Activity },
  { url: 'http://pipeline.localhost', title: '数据流水线', eyebrow: '全链路运行', description: '查看数据从接入、校验、加工到评分发布的完整运行状态。', tags: ['任务运行', '血缘关系', '异常日志'], icon: GitBranch },
];

const flow = ['原始数据', '质量校验', '统一数仓', '经营指标', '客户特征', '模型训练', '客户评分', '营销决策'];

export default function Home() {
  const dark = false;
  const [capacity, setCapacity] = useState(2000);
  const simulation = useMemo(() => {
    const rate = 0.226 - Math.min(capacity / 100000, 0.055);
    const conversions = Math.round(capacity * rate);
    const randomConversions = Math.round(capacity * 0.117);
    const cost = capacity * 18;
    const revenue = conversions * 680;
    return { rate, conversions, randomConversions, lift: conversions / randomConversions, roi: (revenue - cost) / cost };
  }, [capacity]);

  return (
    <div className={dark ? 'dark' : ''}>
      <main className="site-shell min-h-screen bg-background text-foreground">
        <header className="nav-shell">
          <a className="brand" href="#top" aria-label="智营平台首页"><span className="brand-mark"><Orbit size={20} /></span><span><b>智营</b><em>客户经营决策平台</em></span></a>
          <nav className="nav-links" aria-label="主导航"><a href="#overview">总览</a><a href="#decision">决策模拟</a><a href="#flow">数据链路</a></nav>
          <div className="nav-actions"><span className="health"><i /> 全部服务正常</span></div>
        </header>

        <section className="hero" id="top">
          <div className="hero-copy">
            <div className="section-kicker"><Sparkles size={14} /> 从数据到行动，一条链路完成</div>
            <h1>把客户预测，<br /><span>变成经营决策。</span></h1>
            <p>统一连接经营分析、客户评分与营销执行。让团队知道该联系谁、联系多少，以及每一笔投入预计带来多少回报。</p>
            <div className="hero-actions"><a className="primary-button" href="#decision">开始决策模拟 <ArrowRight size={17} /></a><a className="secondary-button" href="#overview">查看平台能力</a></div>
            <div className="trust-row"><span><ShieldCheck size={16} /> 训练字段防泄漏校验</span><span><Database size={16} /> 统一业务数据口径</span></div>
          </div>

          <div className="decision-pulse" id="decision">
            <div className="pulse-head"><div><span>今日决策模拟</span><h2>营销容量</h2></div><div className="live-tag"><i /> 实时计算</div></div>
            <div className="capacity-value"><strong>{capacity.toLocaleString('zh-CN')}</strong><span>位客户</span></div>
            <input aria-label="营销容量" type="range" min="500" max="10000" step="500" value={capacity} onChange={(event) => setCapacity(Number(event.target.value))} />
            <div className="range-labels"><span>500</span><span>10,000</span></div>
            <div className="pulse-grid">
              <div><span>预计转化</span><strong>{simulation.conversions}</strong><small>模型策略</small></div>
              <div><span>平均概率</span><strong>{(simulation.rate * 100).toFixed(1)}%</strong><small>优先客户</small></div>
              <div><span>策略增益</span><strong>{simulation.lift.toFixed(2)}×</strong><small>较随机触达</small></div>
              <div><span>预计回报率</span><strong>{(simulation.roi * 100).toFixed(0)}%</strong><small>扣除触达成本</small></div>
            </div>
            <div className="strategy-compare"><div><span>模型策略</span><b style={{ width: `${Math.min(simulation.conversions / 5, 100)}%` }} /></div><div><span>随机触达</span><b style={{ width: `${Math.min(simulation.randomConversions / 5, 100)}%` }} /></div></div>
            <a className="full-button" href="http://decision.localhost">生成优先客户名单 <ChevronRight size={17} /></a>
          </div>
        </section>

        <section className="metric-strip" aria-label="核心指标"><div><span>可分析客户记录</span><strong>45,211</strong></div><div><span>已接入业务模块</span><strong>06</strong></div><div><span>数据质量规则</span><strong>28</strong></div><div><span>全链路任务成功率</span><strong>99.8%</strong></div></section>

        <section className="content-section" id="overview">
          <div className="section-heading"><div><span>统一工作台</span><h2>六个环节，一套经营语言</h2></div><p>每个模块承担清晰的业务职责，共享同一套数据口径与客户评分结果。</p></div>
          <div className="module-grid">
            {modules.map((module) => { const Icon = module.icon; return <article className={`module-card ${module.featured ? 'featured' : ''}`} key={module.title}>
              <div className="card-top"><span className="module-icon"><Icon size={20} /></span><span className="status"><i /> 运行正常</span></div><span className="card-eyebrow">{module.eyebrow}</span><h3>{module.title}</h3><p>{module.description}</p><div className="tag-row">{module.tags.map((tag) => <span key={tag}>{tag}</span>)}</div><a className="card-link" href={module.url}>进入模块 <ArrowRight size={16} /></a>
            </article>; })}
          </div>
        </section>

        <section className="flow-section" id="flow">
          <div className="flow-intro"><span>数据如何产生价值</span><h2>每个结果，都能回到它的来源。</h2><p>从原始客户记录到最终营销名单，所有加工、训练和评分步骤都可追踪、可复现、可检查。</p><div className="flow-assurances"><span><CheckCircle2 size={16} /> 禁用通话后字段</span><span><CheckCircle2 size={16} /> 概率评分而非简单分类</span><span><CheckCircle2 size={16} /> 按容量动态选择客户</span></div></div>
          <div className="flow-track">{flow.map((item, index) => <div className="flow-node" key={item}><span>{String(index + 1).padStart(2, '0')}</span><b>{item}</b>{index < flow.length - 1 && <i />}</div>)}</div>
        </section>

        <section className="data-note-section" id="data">
          <div className="data-note-head"><span>数据说明</span><h2>每个数字，都有清晰的来路</h2><p>平台使用一份本地保存的公开银行营销历史记录（45,211 条客户联系样本），不依赖在线接口。每行代表一次客户营销联系，标签是活动后是否认购定期存款，用于演示“描述分析 → 概率建模 → 容量决策”的完整闭环。</p><p>原始字段包括：年龄、职业、婚姻、教育、违约、账户余额、住房贷款、个人贷款、联系渠道、联系日、联系月份、本次联系次数、距上次联系天数、历史联系次数、上次活动结果，以及历史标签 y。通话时长 duration 只用于历史分析，预测新客户时明确排除，避免把通话后信息泄露给模型。</p></div>
          <div className="data-note-grid"><article><strong>45,211</strong><span>条历史营销联系记录</span><p>包含客户画像、账户余额、联系渠道、营销月份、历史联系结果与本次是否认购。</p></article><article><strong>15</strong><span>个可用于训练的字段</span><p>训练前会统一校验字段类型、取值范围和可用阶段，通话后才知道的信息不会进入模型。</p></article><article><strong>3 层</strong><span>数据与模型验证</span><p>原始数据质量、数仓指标口径、模型排序效果分别检查，确保分析结果可以解释和复现。</p></article></div>
        </section>

        <footer><div className="brand compact"><span className="brand-mark"><Orbit size={18} /></span><span><b>智营</b><em>客户经营决策平台</em></span></div><p>让每一次客户触达，都有数据依据。</p><span>演示环境 · 数据已脱敏</span></footer>
      </main>
    </div>
  );
}

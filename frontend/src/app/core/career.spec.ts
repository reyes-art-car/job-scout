import { TestBed } from '@angular/core/testing';
import { offer, PROFILE } from '../../testing/fixtures';
import { CareerService } from './career.service';
import { analyzeForCareer, emptyCareer, enrichedProfile, fitWarnings, followUpDate, offerKey, profileLevels, safeEvidenceUrl } from './career';
import { validateCareer } from './career-validation';
import { buildCoverLetter } from './cover-letter';
import { tailorCv } from './tailoring';

describe('Evidence-based matching', () => {
  it('uses the actual profile rather than the catalog candidate levels', () => {
    const levels = profileLevels(PROFILE, emptyCareer());
    expect(levels['java']).toBe('have');
    expect(levels['kafka']).toBe('gap');
    expect(levels['mysql']).toBe('gap');
  });
  it('reweights corrected requirements and can restore original detection', () => {
    const data = emptyCareer();
    const job = offer({ title: 'Developer', mandatory_tech: 'Java, Kafka', desirable_tech: '' });
    const key = offerKey(job, 'demo');
    expect(analyzeForCareer(PROFILE, data, job, 'demo').coverage).toBe(50);
    data.corrections[key] = { kafka: 'deseable' };
    expect(analyzeForCareer(PROFILE, data, job, 'demo').coverage).toBe(75);
    data.corrections[key] = { kafka: 'ignorar' };
    expect(analyzeForCareer(PROFILE, data, job, 'demo').coverage).toBe(100);
    expect(analyzeForCareer(PROFILE, data, job, 'api').coverage).toBe(50);
  });
  it('returns zero coverage for no recognized requirements', () => {
    expect(analyzeForCareer(PROFILE, emptyCareer(), offer({ title: 'Developer', mandatory_tech: '', desirable_tech: '' }), 'demo').coverage).toBe(0);
  });
  it('does not promote a completed practice to a confirmed competency', () => {
    const data = emptyCareer();
    data.skills['kafka'] = { stage: 'completado', level: 'gap' };
    expect(profileLevels(PROFILE, data)['kafka']).toBe('gap');
    data.skills['kafka'].level = 'have';
    expect(profileLevels(PROFILE, data)['kafka']).toBe('partial');
  });
  it('only includes explicitly confirmed evidence in the tailored CV', () => {
    const data = emptyCareer();
    data.evidence.push({ id: 'e', techId: 'kafka', title: 'Event consumer', description: 'Built a tested consumer', url: '', createdAt: new Date().toISOString() });
    expect(enrichedProfile(PROFILE, data).bullets.length).toBe(PROFILE.bullets.length);
    data.skills['kafka'] = { stage: 'completado', level: 'have' };
    const profile = enrichedProfile(PROFILE, data);
    const job = offer({ mandatory_tech: 'Kafka', desirable_tech: '' });
    const analysis = analyzeForCareer(PROFILE, data, job, 'demo');
    const cv = tailorCv(profile, job, '', profileLevels(PROFILE, data), analysis);
    expect(cv.bullets.some(b => b.text.includes('Built a tested consumer'))).toBeTrue();
    expect(cv.groups.some(g => g.items.some(i => i.text === 'Apache Kafka'))).toBeTrue();
  });
  it('removes contradicted profile claims and does not invent fallback technologies', () => {
    const data = emptyCareer();
    data.skills['java'] = { stage: 'pendiente', level: 'gap' };
    const job = offer({ title: 'Developer', mandatory_tech: 'Kafka', desirable_tech: '' });
    const analysis = analyzeForCareer(PROFILE, data, job, 'demo');
    const cv = tailorCv(enrichedProfile(PROFILE, data), job, '', profileLevels(PROFILE, data), analysis);
    expect(cv.title).not.toContain('JAVA');
    expect(cv.groups.flatMap(g => g.items).some(i => i.text === 'Java')).toBeFalse();
    expect(cv.bullets.some(b => b.text === PROFILE.bullets[0].text)).toBeFalse();
  });
});

describe('Evidence-based cover letters', () => {
  it('uses reviewed competencies and the candidate statements without a hardcoded biography', () => {
    const data = emptyCareer();
    const job = offer({ mandatory_tech: 'Java, Kafka', desirable_tech: '' });
    const letter = buildCoverLetter(enrichedProfile(PROFILE, data), job, {
      tone: 'formal', mentionGaps: true, availability: 'en dos semanas',
      analysis: analyzeForCareer(PROFILE, data, job, 'demo'),
    });
    const text = letter.paragraphs.join(' ');
    expect(text).toContain('CRM en producción');
    expect(text).not.toContain('Freelance');
    expect(text).not.toContain('trabajo a diario');
    expect(text).toContain('Todavía no puedo acreditar Apache Kafka');
    expect(letter.closing).toContain('en dos semanas');
  });
});

describe('Eligibility warnings', () => {
  const preferences = { experienceYears: 1, location: 'Sevilla', remoteOnly: true };
  it('separates technical match from experience and territorial restrictions', () => {
    const warnings = fitWarnings(offer({ experience_required: '3-5 años', location: 'Madrid', modality: 'Presencial' }), preferences);
    expect(warnings.map(w => w.kind)).toEqual(['experience', 'remote', 'location']);
    expect(warnings[0].text).toContain('3 años');
  });
  it('does not treat unspecified experience as zero', () => {
    expect(fitWarnings(offer({ experience_required: 'No especificado' }), { ...preferences, location: '', remoteOnly: false }).some(w => w.kind === 'unknown')).toBeTrue();
  });
  it('flags senior titles even without an explicit minimum', () => {
    expect(fitWarnings(offer({ title: 'Senior Java developer' }), preferences).some(w => w.kind === 'seniority')).toBeTrue();
  });
  it('calculates follow-up dates across month boundaries and rejects impossible dates', () => {
    expect(followUpDate('2026-01-29')).toBe('2026-02-05');
    expect(() => followUpDate('2026-02-30')).toThrow();
  });
});

describe('Career persistence and snapshots', () => {
  let career: CareerService;
  let previous: string | null;
  let writeSpy: jasmine.Spy | undefined;
  beforeEach(() => {
    writeSpy = undefined;
    previous = localStorage.getItem('jobscout.career.v1');
    localStorage.removeItem('jobscout.career.v1');
    TestBed.configureTestingModule({});
    career = TestBed.inject(CareerService);
  });
  afterEach(() => {
    writeSpy?.and.callThrough();
    if (previous === null) localStorage.removeItem('jobscout.career.v1');
    else localStorage.setItem('jobscout.career.v1', previous);
  });
  it('rejects executable and credential-bearing evidence URLs', () => {
    expect(() => safeEvidenceUrl('javascript:alert(1)')).toThrow();
    expect(() => safeEvidenceUrl('https://user:password@example.com')).toThrow();
    expect(safeEvidenceUrl('https://github.com/ada/project')).toContain('github.com');
  });
  it('requires evidence before promoting a competency and downgrades it after removal', () => {
    expect(() => career.setSkill('kafka', 'completado', 'have')).toThrow();
    career.addEvidence({ techId: 'kafka', title: 'Consumer', description: 'Tests and documentation', url: '' });
    career.setSkill('kafka', 'completado', 'have');
    career.removeEvidence(career.data().evidence[0].id);
    expect(career.data().skills['kafka'].level).toBe('partial');
  });
  it('keeps saved CV versions immutable and distinguishes draft from sent', () => {
    const job = offer();
    career.saveCv(job, 'demo', 'Original text', '<p>Original text</p>', null);
    career.saveCv(job, 'demo', 'Edited text', '<p>Edited text</p>', '2026-10-17');
    expect(career.data().snapshots[0].text).toBe('Original text');
    expect(career.data().snapshots[0].appliedOn).toBeNull();
    expect(career.data().snapshots[1].followUpOn).toBe('2026-10-24');
    expect(validateCareer(JSON.parse(career.exportBackup())).snapshots).toHaveSize(2);
  });
  it('records actual state transitions only and separates demo from API', () => {
    const job = offer({ kanban_status: 'Pendiente' });
    career.recordStatus(job, 'demo', 'Pendiente');
    expect(career.data().events).toHaveSize(0);
    career.recordStatus(job, 'api', 'Aplicado');
    expect(career.data().events[0].offerKey).toBe(offerKey(job, 'api'));
    expect(offerKey(job, 'api')).not.toBe(offerKey(job, 'demo'));
  });
  it('rejects invalid backups without replacing current data', () => {
    career.setPreferences({ experienceYears: 2, location: 'Sevilla', remoteOnly: true });
    const before = career.exportBackup();
    expect(() => career.importBackup('{"version":1}')).toThrow();
    expect(career.exportBackup()).toBe(before);
    const data = emptyCareer();
    data.preferences.experienceYears = -1;
    expect(() => validateCareer(data)).toThrow();
  });
  it('restores stored data and reports write failures without losing in-memory progress', () => {
    career.addEvidence({ techId: 'java', title: 'Project', description: 'Implemented a service', url: '' });
    const restored = new CareerService();
    expect(restored.data().evidence).toHaveSize(1);
    writeSpy = spyOn(localStorage, 'setItem').and.throwError('Quota exceeded');
    career.setPreferences({ experienceYears: 2, location: '', remoteOnly: false });
    expect(career.data().preferences.experienceYears).toBe(2);
    expect(career.notice()).toContain('Exporta');
  });
  it('rejects unsafe URLs in imported evidence too', () => {
    const data = emptyCareer();
    data.evidence.push({ id: 'e', techId: 'java', title: 'x', description: 'x', url: 'javascript:alert(1)', createdAt: new Date().toISOString() });
    expect(() => career.importBackup(JSON.stringify(data))).toThrow();
    data.evidence[0].url = '';
    data.evidence[0].description = ' ';
    expect(() => career.importBackup(JSON.stringify(data))).toThrow();
  });
});

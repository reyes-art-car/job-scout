import { detectTechs } from './tech-catalog';

const ids = (text: string) => detectTechs(text).map((t) => t.id);

describe('detectTechs', () => {
  it('no confunde Java con JavaScript', () => {
    expect(ids('JavaScript y TypeScript')).toEqual(jasmine.arrayContaining(['javascript', 'typescript']));
    expect(ids('JavaScript')).not.toContain('java');
  });

  it('distingue Spring Boot, Spring Cloud y Spring genérico', () => {
    expect(ids('Spring Boot')).toEqual(['spring-boot']);
    expect(ids('Spring Cloud')).toContain('spring-cloud');
    expect(ids('Spring Cloud')).not.toContain('cloud');
    expect(ids('Spring Cloud')).not.toContain('spring');
    expect(ids('Spring')).toContain('spring');
  });

  it('reconoce variantes de CI/CD, REST y microservicios', () => {
    expect(ids('CI/CD con GitHub Actions')).toContain('ci-cd');
    expect(ids('APIs REST')).toContain('rest');
    expect(ids('arquitectura de microservicios')).toContain('microservices');
  });

  it('NoSQL no cuenta como SQL y MySQL no cuenta como SQL', () => {
    expect(ids('MongoDB, NoSQL')).not.toContain('sql');
    expect(ids('MySQL')).toEqual(['mysql']);
  });

  it('no detecta AngularJS como Angular', () => {
    expect(ids('AngularJS')).not.toContain('angular');
    expect(ids('Angular 18+')).toContain('angular');
  });

  it('devuelve vacío para texto vacío', () => {
    expect(detectTechs('')).toEqual([]);
  });
});

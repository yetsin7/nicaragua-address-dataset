-- ============================================================
-- Tabla principal de direcciones de Nicaragua
-- Proyecto: nicaragua-address-dataset → CocibolkaDB (Supabase)
-- ============================================================

CREATE TABLE IF NOT EXISTS public.nicaragua_direcciones (
    id            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    departamento  TEXT    NOT NULL,
    municipio     TEXT    NOT NULL,
    comunidad     TEXT,                        -- comarca o comunidad rural
    barrio        TEXT,                        -- barrio urbano
    calle         TEXT,                        -- calle o avenida (se añade después)
    cod_postal    INTEGER NOT NULL,
    cod_municipio INTEGER,
    cod_barrio    INTEGER,
    es_maestro    BOOLEAN NOT NULL DEFAULT FALSE,  -- TRUE = entrada de código maestro
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Índices para búsquedas frecuentes
CREATE INDEX IF NOT EXISTS idx_nic_dir_departamento  ON public.nicaragua_direcciones(departamento);
CREATE INDEX IF NOT EXISTS idx_nic_dir_municipio     ON public.nicaragua_direcciones(municipio);
CREATE INDEX IF NOT EXISTS idx_nic_dir_cod_postal    ON public.nicaragua_direcciones(cod_postal);
CREATE INDEX IF NOT EXISTS idx_nic_dir_barrio        ON public.nicaragua_direcciones(barrio);

-- RLS: lectura pública, escritura solo autenticada
ALTER TABLE public.nicaragua_direcciones ENABLE ROW LEVEL SECURITY;

CREATE POLICY "lectura_publica"
    ON public.nicaragua_direcciones FOR SELECT
    USING (true);

CREATE POLICY "escritura_autenticada"
    ON public.nicaragua_direcciones FOR ALL
    USING (auth.role() = 'service_role');

COMMENT ON TABLE public.nicaragua_direcciones IS
    'Dataset de direcciones postales de Nicaragua. Fuente: Correos de Nicaragua / INIDE.';

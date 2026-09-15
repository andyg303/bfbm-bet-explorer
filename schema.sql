--
-- BFBM Bet Explorer — canonical PostgreSQL schema.
--
-- This file is checked in so we can track what production *should* look like.
-- It is NOT applied automatically; the live schema is created by SQLAlchemy
-- via init_db() in backend/database.py and evolved by one-off migration
-- scripts in backend/scripts/ (e.g. add_performance_indexes.py).
--
-- To regenerate after a schema change:
--   docker compose exec -T -e PGPASSWORD="$DB_PASSWORD" db \
--     pg_dump -U "$DB_USER" -d "$DB_NAME" --schema-only --no-owner --no-privileges \
--     | sed -E '/^\\(restrict|unrestrict) /d' > schema.sql
--
--
-- PostgreSQL database dump
--


-- Dumped from database version 16.13
-- Dumped by pg_dump version 16.13

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: automation_tokens; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.automation_tokens (
    id integer NOT NULL,
    user_id integer NOT NULL,
    name character varying NOT NULL,
    token_hash character varying NOT NULL,
    token_prefix character varying NOT NULL,
    created_at timestamp without time zone NOT NULL,
    last_used_at timestamp without time zone,
    revoked_at timestamp without time zone
);


--
-- Name: automation_tokens_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.automation_tokens_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: automation_tokens_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.automation_tokens_id_seq OWNED BY public.automation_tokens.id;


--
-- Name: bets; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.bets (
    id integer NOT NULL,
    user_id integer,
    bet_id character varying,
    event character varying,
    country_code character varying,
    competition character varying,
    favorite_position integer,
    description character varying,
    selection character varying,
    bet_type character varying,
    matched_amount double precision,
    loss_rec_amount double precision,
    avg_price_matched double precision,
    price_requested double precision,
    status character varying,
    profit_loss double precision,
    strategy character varying,
    bsp double precision,
    total_matched_on_runner double precision,
    total_matched_on_market double precision,
    short_description character varying,
    tipster character varying,
    placed_date timestamp without time zone,
    matched_date timestamp without time zone,
    settled_date timestamp without time zone,
    number_of_selections integer,
    market_type character varying,
    lay_liability double precision,
    bsp_diff_absolute double precision,
    bsp_diff_percentage double precision,
    bsp_diff_probability double precision,
    is_deleted boolean,
    is_archived boolean,
    market_name character varying,
    market_id character varying,
    start_time timestamp without time zone,
    strategy_id character varying,
    commission_paid double precision DEFAULT 0.0
);


--
-- Name: bets_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.bets_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: bets_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.bets_id_seq OWNED BY public.bets.id;


--
-- Name: ingestion_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ingestion_logs (
    id integer NOT NULL,
    user_id integer NOT NULL,
    filename character varying NOT NULL,
    status character varying NOT NULL,
    rows_total integer,
    rows_inserted integer,
    rows_updated integer,
    rows_skipped integer,
    error_message character varying,
    warnings character varying,
    created_at timestamp without time zone NOT NULL
);


--
-- Name: ingestion_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.ingestion_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: ingestion_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.ingestion_logs_id_seq OWNED BY public.ingestion_logs.id;


--
-- Name: strategy_favorites; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.strategy_favorites (
    id integer NOT NULL,
    user_id integer NOT NULL,
    strategy character varying NOT NULL,
    created_at timestamp without time zone NOT NULL
);


--
-- Name: strategy_favorites_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.strategy_favorites_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: strategy_favorites_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.strategy_favorites_id_seq OWNED BY public.strategy_favorites.id;


--
-- Name: strategy_group_members; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.strategy_group_members (
    id integer NOT NULL,
    group_id integer NOT NULL,
    strategy character varying NOT NULL
);


--
-- Name: strategy_group_members_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.strategy_group_members_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: strategy_group_members_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.strategy_group_members_id_seq OWNED BY public.strategy_group_members.id;


--
-- Name: strategy_groups; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.strategy_groups (
    id integer NOT NULL,
    user_id integer NOT NULL,
    name character varying NOT NULL,
    created_at timestamp without time zone NOT NULL
);


--
-- Name: strategy_groups_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.strategy_groups_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: strategy_groups_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.strategy_groups_id_seq OWNED BY public.strategy_groups.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users (
    id integer NOT NULL,
    email character varying NOT NULL,
    password_hash character varying NOT NULL,
    display_name character varying,
    is_active boolean NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone,
    password_reset_token character varying,
    password_reset_expires timestamp without time zone,
    subscription_status character varying NOT NULL,
    subscription_plan character varying,
    subscription_start timestamp without time zone,
    subscription_expires timestamp without time zone,
    stripe_customer_id character varying,
    stripe_checkout_session_id character varying,
    is_admin boolean DEFAULT false NOT NULL,
    token_version integer DEFAULT 0 NOT NULL,
    failed_login_attempts integer DEFAULT 0 NOT NULL,
    locked_until timestamp without time zone,
    password_reset_token_id character varying,
    commission_rate double precision DEFAULT 2.0 NOT NULL,
    commission_rate_aus_nz double precision DEFAULT 5.0 NOT NULL,
    referral_code character varying,
    referred_by_user_id integer,
    referral_rewarded_at timestamp without time zone,
    referral_credit_balance integer DEFAULT 0 NOT NULL,
    referral_credits_awarded integer DEFAULT 0 NOT NULL,
    referral_credits_redeemed integer DEFAULT 0 NOT NULL,
    referral_pending_checkout_session_id character varying,
    referral_last_redeemed_session_id character varying
);


--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: automation_tokens id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.automation_tokens ALTER COLUMN id SET DEFAULT nextval('public.automation_tokens_id_seq'::regclass);


--
-- Name: bets id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bets ALTER COLUMN id SET DEFAULT nextval('public.bets_id_seq'::regclass);


--
-- Name: ingestion_logs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ingestion_logs ALTER COLUMN id SET DEFAULT nextval('public.ingestion_logs_id_seq'::regclass);


--
-- Name: strategy_favorites id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.strategy_favorites ALTER COLUMN id SET DEFAULT nextval('public.strategy_favorites_id_seq'::regclass);


--
-- Name: strategy_group_members id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.strategy_group_members ALTER COLUMN id SET DEFAULT nextval('public.strategy_group_members_id_seq'::regclass);


--
-- Name: strategy_groups id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.strategy_groups ALTER COLUMN id SET DEFAULT nextval('public.strategy_groups_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Name: automation_tokens automation_tokens_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.automation_tokens
    ADD CONSTRAINT automation_tokens_pkey PRIMARY KEY (id);


--
-- Name: bets bets_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bets
    ADD CONSTRAINT bets_pkey PRIMARY KEY (id);


--
-- Name: ingestion_logs ingestion_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ingestion_logs
    ADD CONSTRAINT ingestion_logs_pkey PRIMARY KEY (id);


--
-- Name: strategy_favorites strategy_favorites_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.strategy_favorites
    ADD CONSTRAINT strategy_favorites_pkey PRIMARY KEY (id);


--
-- Name: strategy_group_members strategy_group_members_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.strategy_group_members
    ADD CONSTRAINT strategy_group_members_pkey PRIMARY KEY (id);


--
-- Name: strategy_groups strategy_groups_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.strategy_groups
    ADD CONSTRAINT strategy_groups_pkey PRIMARY KEY (id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: idx_bet_type_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_bet_type_status ON public.bets USING btree (bet_type, status);


--
-- Name: idx_bets_user_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_bets_user_active ON public.bets USING btree (user_id) WHERE ((is_deleted = false) AND (is_archived = false));


--
-- Name: idx_bets_user_starttime; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_bets_user_starttime ON public.bets USING btree (user_id, start_time) WHERE ((is_deleted = false) AND (is_archived = false));


--
-- Name: idx_strategy_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_strategy_date ON public.bets USING btree (strategy, settled_date);


--
-- Name: idx_user_bet_id; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_user_bet_id ON public.bets USING btree (user_id, bet_id);


--
-- Name: idx_user_strategy; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_strategy ON public.bets USING btree (user_id, strategy);


--
-- Name: ix_automation_tokens_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_automation_tokens_id ON public.automation_tokens USING btree (id);


--
-- Name: ix_automation_tokens_revoked_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_automation_tokens_revoked_at ON public.automation_tokens USING btree (revoked_at);


--
-- Name: ix_automation_tokens_token_hash; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_automation_tokens_token_hash ON public.automation_tokens USING btree (token_hash);


--
-- Name: ix_automation_tokens_token_prefix; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_automation_tokens_token_prefix ON public.automation_tokens USING btree (token_prefix);


--
-- Name: ix_automation_tokens_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_automation_tokens_user_id ON public.automation_tokens USING btree (user_id);


--
-- Name: ix_bets_bet_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_bets_bet_id ON public.bets USING btree (bet_id);


--
-- Name: ix_bets_bet_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_bets_bet_type ON public.bets USING btree (bet_type);


--
-- Name: ix_bets_competition; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_bets_competition ON public.bets USING btree (competition);


--
-- Name: ix_bets_country_code; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_bets_country_code ON public.bets USING btree (country_code);


--
-- Name: ix_bets_event; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_bets_event ON public.bets USING btree (event);


--
-- Name: ix_bets_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_bets_id ON public.bets USING btree (id);


--
-- Name: ix_bets_is_archived; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_bets_is_archived ON public.bets USING btree (is_archived);


--
-- Name: ix_bets_is_deleted; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_bets_is_deleted ON public.bets USING btree (is_deleted);


--
-- Name: ix_bets_market_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_bets_market_type ON public.bets USING btree (market_type);


--
-- Name: ix_bets_matched_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_bets_matched_date ON public.bets USING btree (matched_date);


--
-- Name: ix_bets_placed_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_bets_placed_date ON public.bets USING btree (placed_date);


--
-- Name: ix_bets_profit_loss; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_bets_profit_loss ON public.bets USING btree (profit_loss);


--
-- Name: ix_bets_selection; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_bets_selection ON public.bets USING btree (selection);


--
-- Name: ix_bets_settled_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_bets_settled_date ON public.bets USING btree (settled_date);


--
-- Name: ix_bets_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_bets_status ON public.bets USING btree (status);


--
-- Name: ix_bets_strategy; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_bets_strategy ON public.bets USING btree (strategy);


--
-- Name: ix_bets_strategy_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_bets_strategy_id ON public.bets USING btree (strategy_id);


--
-- Name: ix_bets_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_bets_user_id ON public.bets USING btree (user_id);


--
-- Name: ix_ingestion_logs_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_ingestion_logs_id ON public.ingestion_logs USING btree (id);


--
-- Name: ix_ingestion_logs_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_ingestion_logs_status ON public.ingestion_logs USING btree (status);


--
-- Name: ix_ingestion_logs_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_ingestion_logs_user_id ON public.ingestion_logs USING btree (user_id);


--
-- Name: ix_strategy_favorites_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_strategy_favorites_id ON public.strategy_favorites USING btree (id);


--
-- Name: ix_strategy_favorites_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_strategy_favorites_user_id ON public.strategy_favorites USING btree (user_id);


--
-- Name: ix_strategy_favorites_user_strategy; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_strategy_favorites_user_strategy ON public.strategy_favorites USING btree (user_id, strategy);


--
-- Name: ix_strategy_group_members_group_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_strategy_group_members_group_id ON public.strategy_group_members USING btree (group_id);


--
-- Name: ix_strategy_group_members_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_strategy_group_members_id ON public.strategy_group_members USING btree (id);


--
-- Name: ix_strategy_group_members_unique; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_strategy_group_members_unique ON public.strategy_group_members USING btree (group_id, strategy);


--
-- Name: ix_strategy_groups_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_strategy_groups_id ON public.strategy_groups USING btree (id);


--
-- Name: ix_strategy_groups_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_strategy_groups_user_id ON public.strategy_groups USING btree (user_id);


--
-- Name: ix_strategy_groups_user_name; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_strategy_groups_user_name ON public.strategy_groups USING btree (user_id, name);


--
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_users_email ON public.users USING btree (email);


--
-- Name: ix_users_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_users_id ON public.users USING btree (id);


--
-- Name: ix_users_password_reset_token; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_users_password_reset_token ON public.users USING btree (password_reset_token);


--
-- Name: ix_users_password_reset_token_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_users_password_reset_token_id ON public.users USING btree (password_reset_token_id);


--
-- Name: ix_users_referral_code; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_users_referral_code ON public.users USING btree (referral_code);


--
-- Name: ix_users_referred_by_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_users_referred_by_user_id ON public.users USING btree (referred_by_user_id);


--
-- Name: ix_users_stripe_customer_id; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_users_stripe_customer_id ON public.users USING btree (stripe_customer_id);


--
-- Name: automation_tokens automation_tokens_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.automation_tokens
    ADD CONSTRAINT automation_tokens_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: bets bets_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bets
    ADD CONSTRAINT bets_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: ingestion_logs ingestion_logs_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ingestion_logs
    ADD CONSTRAINT ingestion_logs_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: strategy_favorites strategy_favorites_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.strategy_favorites
    ADD CONSTRAINT strategy_favorites_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: strategy_group_members strategy_group_members_group_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.strategy_group_members
    ADD CONSTRAINT strategy_group_members_group_id_fkey FOREIGN KEY (group_id) REFERENCES public.strategy_groups(id) ON DELETE CASCADE;


--
-- Name: strategy_groups strategy_groups_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.strategy_groups
    ADD CONSTRAINT strategy_groups_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: users users_referred_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_referred_by_user_id_fkey FOREIGN KEY (referred_by_user_id) REFERENCES public.users(id);


--
-- PostgreSQL database dump complete
--



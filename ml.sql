--
-- PostgreSQL database dump
--

-- Dumped from database version 12.14
-- Dumped by pg_dump version 12.14

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
-- Name: icons; Type: TABLE; Schema: public; Owner: ml
--

CREATE TABLE public.icons (
    id integer NOT NULL,
    icon bytea NOT NULL
);


ALTER TABLE public.icons OWNER TO ml;

--
-- Name: icons_id_seq; Type: SEQUENCE; Schema: public; Owner: ml
--

CREATE SEQUENCE public.icons_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.icons_id_seq OWNER TO ml;

--
-- Name: icons_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: ml
--

ALTER SEQUENCE public.icons_id_seq OWNED BY public.icons.id;


--
-- Name: league_members; Type: TABLE; Schema: public; Owner: netllama
--

CREATE TABLE public.league_members (
    id integer NOT NULL,
    league_id integer NOT NULL,
    user_id integer NOT NULL
);


ALTER TABLE public.league_members OWNER TO netllama;

--
-- Name: league_members_id_seq; Type: SEQUENCE; Schema: public; Owner: netllama
--

CREATE SEQUENCE public.league_members_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.league_members_id_seq OWNER TO netllama;

--
-- Name: league_members_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: netllama
--

ALTER SEQUENCE public.league_members_id_seq OWNED BY public.league_members.id;


--
-- Name: leagues; Type: TABLE; Schema: public; Owner: ml
--

CREATE TABLE public.leagues (
    id integer NOT NULL,
    name text NOT NULL,
    submit_days integer NOT NULL,
    vote_days integer NOT NULL,
    descr text,
    end_date timestamp without time zone NOT NULL,
    upvotes integer DEFAULT 10 NOT NULL,
    downvotes integer DEFAULT 0 NOT NULL,
    owner_id integer NOT NULL,
    round_count integer DEFAULT 1 NOT NULL,
    CONSTRAINT positive_round_cnt CHECK ((round_count > 0))
);


ALTER TABLE public.leagues OWNER TO ml;

--
-- Name: leagues_id_seq; Type: SEQUENCE; Schema: public; Owner: ml
--

CREATE SEQUENCE public.leagues_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.leagues_id_seq OWNER TO ml;

--
-- Name: leagues_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: ml
--

ALTER SEQUENCE public.leagues_id_seq OWNED BY public.leagues.id;


--
-- Name: rounds; Type: TABLE; Schema: public; Owner: ml
--

CREATE TABLE public.rounds (
    id integer NOT NULL,
    league_id integer NOT NULL,
    name text NOT NULL,
    descr text NOT NULL,
    end_date timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.rounds OWNER TO ml;

--
-- Name: rounds_id_seq; Type: SEQUENCE; Schema: public; Owner: ml
--

CREATE SEQUENCE public.rounds_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.rounds_id_seq OWNER TO ml;

--
-- Name: rounds_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: ml
--

ALTER SEQUENCE public.rounds_id_seq OWNED BY public.rounds.id;


--
-- Name: songs; Type: TABLE; Schema: public; Owner: ml
--

CREATE TABLE public.songs (
    id integer NOT NULL,
    league_id integer NOT NULL,
    song_url text NOT NULL,
    descr text,
    round_id integer NOT NULL,
    user_id integer NOT NULL,
    title text NOT NULL,
    thumbnail text NOT NULL,
    video_id text NOT NULL
);


ALTER TABLE public.songs OWNER TO ml;

--
-- Name: songs_id_seq; Type: SEQUENCE; Schema: public; Owner: ml
--

CREATE SEQUENCE public.songs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.songs_id_seq OWNER TO ml;

--
-- Name: songs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: ml
--

ALTER SEQUENCE public.songs_id_seq OWNED BY public.songs.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: ml
--

CREATE TABLE public.users (
    id integer NOT NULL,
    username text NOT NULL,
    email text NOT NULL,
    passwd text NOT NULL,
    name text NOT NULL,
    active boolean DEFAULT true NOT NULL,
    icon_id integer,
    last_login date DEFAULT now() NOT NULL
);


ALTER TABLE public.users OWNER TO ml;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: ml
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.users_id_seq OWNER TO ml;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: ml
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: votes; Type: TABLE; Schema: public; Owner: ml
--

CREATE TABLE public.votes (
    id integer NOT NULL,
    song_id integer NOT NULL,
    league_id integer NOT NULL,
    user_id integer NOT NULL,
    votes integer DEFAULT 0 NOT NULL,
    comment text,
    vote_date timestamp without time zone DEFAULT now() NOT NULL,
    round_id integer NOT NULL
);


ALTER TABLE public.votes OWNER TO ml;

--
-- Name: votes_id_seq; Type: SEQUENCE; Schema: public; Owner: ml
--

CREATE SEQUENCE public.votes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.votes_id_seq OWNER TO ml;

--
-- Name: votes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: ml
--

ALTER SEQUENCE public.votes_id_seq OWNED BY public.votes.id;


--
-- Name: icons id; Type: DEFAULT; Schema: public; Owner: ml
--

ALTER TABLE ONLY public.icons ALTER COLUMN id SET DEFAULT nextval('public.icons_id_seq'::regclass);


--
-- Name: league_members id; Type: DEFAULT; Schema: public; Owner: netllama
--

ALTER TABLE ONLY public.league_members ALTER COLUMN id SET DEFAULT nextval('public.league_members_id_seq'::regclass);


--
-- Name: leagues id; Type: DEFAULT; Schema: public; Owner: ml
--

ALTER TABLE ONLY public.leagues ALTER COLUMN id SET DEFAULT nextval('public.leagues_id_seq'::regclass);


--
-- Name: rounds id; Type: DEFAULT; Schema: public; Owner: ml
--

ALTER TABLE ONLY public.rounds ALTER COLUMN id SET DEFAULT nextval('public.rounds_id_seq'::regclass);


--
-- Name: songs id; Type: DEFAULT; Schema: public; Owner: ml
--

ALTER TABLE ONLY public.songs ALTER COLUMN id SET DEFAULT nextval('public.songs_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: ml
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Name: votes id; Type: DEFAULT; Schema: public; Owner: ml
--

ALTER TABLE ONLY public.votes ALTER COLUMN id SET DEFAULT nextval('public.votes_id_seq'::regclass);


--
-- Name: icons icons_pkey; Type: CONSTRAINT; Schema: public; Owner: ml
--

ALTER TABLE ONLY public.icons
    ADD CONSTRAINT icons_pkey PRIMARY KEY (id);


--
-- Name: league_members league_members_pkey; Type: CONSTRAINT; Schema: public; Owner: netllama
--

ALTER TABLE ONLY public.league_members
    ADD CONSTRAINT league_members_pkey PRIMARY KEY (id);


--
-- Name: leagues leagues_pkey; Type: CONSTRAINT; Schema: public; Owner: ml
--

ALTER TABLE ONLY public.leagues
    ADD CONSTRAINT leagues_pkey PRIMARY KEY (id);


--
-- Name: rounds rounds_pkey; Type: CONSTRAINT; Schema: public; Owner: ml
--

ALTER TABLE ONLY public.rounds
    ADD CONSTRAINT rounds_pkey PRIMARY KEY (id);


--
-- Name: songs songs_pkey; Type: CONSTRAINT; Schema: public; Owner: ml
--

ALTER TABLE ONLY public.songs
    ADD CONSTRAINT songs_pkey PRIMARY KEY (id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: ml
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: users users_username_key; Type: CONSTRAINT; Schema: public; Owner: ml
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_username_key UNIQUE (username);


--
-- Name: votes votes_pkey; Type: CONSTRAINT; Schema: public; Owner: ml
--

ALTER TABLE ONLY public.votes
    ADD CONSTRAINT votes_pkey PRIMARY KEY (id);


--
-- Name: users fk_icon_id; Type: FK CONSTRAINT; Schema: public; Owner: ml
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT fk_icon_id FOREIGN KEY (icon_id) REFERENCES public.icons(id);


--
-- Name: songs fk_league_id; Type: FK CONSTRAINT; Schema: public; Owner: ml
--

ALTER TABLE ONLY public.songs
    ADD CONSTRAINT fk_league_id FOREIGN KEY (league_id) REFERENCES public.leagues(id);


--
-- Name: votes fk_league_id; Type: FK CONSTRAINT; Schema: public; Owner: ml
--

ALTER TABLE ONLY public.votes
    ADD CONSTRAINT fk_league_id FOREIGN KEY (league_id) REFERENCES public.leagues(id);


--
-- Name: rounds fk_league_id; Type: FK CONSTRAINT; Schema: public; Owner: ml
--

ALTER TABLE ONLY public.rounds
    ADD CONSTRAINT fk_league_id FOREIGN KEY (league_id) REFERENCES public.leagues(id);


--
-- Name: league_members fk_league_id; Type: FK CONSTRAINT; Schema: public; Owner: netllama
--

ALTER TABLE ONLY public.league_members
    ADD CONSTRAINT fk_league_id FOREIGN KEY (league_id) REFERENCES public.leagues(id);


--
-- Name: leagues fk_owner_id; Type: FK CONSTRAINT; Schema: public; Owner: ml
--

ALTER TABLE ONLY public.leagues
    ADD CONSTRAINT fk_owner_id FOREIGN KEY (owner_id) REFERENCES public.users(id);


--
-- Name: songs fk_round_id; Type: FK CONSTRAINT; Schema: public; Owner: ml
--

ALTER TABLE ONLY public.songs
    ADD CONSTRAINT fk_round_id FOREIGN KEY (round_id) REFERENCES public.rounds(id);


--
-- Name: votes fk_round_id; Type: FK CONSTRAINT; Schema: public; Owner: ml
--

ALTER TABLE ONLY public.votes
    ADD CONSTRAINT fk_round_id FOREIGN KEY (round_id) REFERENCES public.rounds(id);


--
-- Name: votes fk_song_id; Type: FK CONSTRAINT; Schema: public; Owner: ml
--

ALTER TABLE ONLY public.votes
    ADD CONSTRAINT fk_song_id FOREIGN KEY (song_id) REFERENCES public.songs(id);


--
-- Name: votes fk_user_id; Type: FK CONSTRAINT; Schema: public; Owner: ml
--

ALTER TABLE ONLY public.votes
    ADD CONSTRAINT fk_user_id FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: league_members fk_user_id; Type: FK CONSTRAINT; Schema: public; Owner: netllama
--

ALTER TABLE ONLY public.league_members
    ADD CONSTRAINT fk_user_id FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: songs fk_user_id; Type: FK CONSTRAINT; Schema: public; Owner: ml
--

ALTER TABLE ONLY public.songs
    ADD CONSTRAINT fk_user_id FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: TABLE league_members; Type: ACL; Schema: public; Owner: netllama
--

GRANT ALL ON TABLE public.league_members TO ml;


--
-- Name: SEQUENCE league_members_id_seq; Type: ACL; Schema: public; Owner: netllama
--

GRANT ALL ON SEQUENCE public.league_members_id_seq TO ml;


--
-- PostgreSQL database dump complete
--


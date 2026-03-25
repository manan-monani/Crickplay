-- Staging Deliveries
-- Extract and flatten delivery events from Bronze layer

{{
    config(
        materialized='table',
        schema='silver'
    )
}}


with source as (
    select * from {{ source('bronze', 'bronze_deliveries') }}
),

flattened as (
    select
        -- Primary keys
        id as bronze_id,
        match_id,

-- Match info
raw_payload ->> 'match_date' as match_date,
raw_payload ->> 'season' as season,
raw_payload ->> 'event_name' as event_name,
raw_payload ->> 'venue' as venue,
raw_payload ->> 'match_type' as match_type,
raw_payload ->> 'gender' as gender,
raw_payload ->> 'team_type' as team_type,

-- Teams
raw_payload ->> 'batting_team' as batting_team,
raw_payload ->> 'bowling_team' as bowling_team,
raw_payload -> 'teams' as teams_array,

-- Toss
raw_payload ->> 'toss_winner' as toss_winner,
raw_payload ->> 'toss_decision' as toss_decision,

-- Delivery position
(
    raw_payload ->> 'innings_number'
)::int as innings_number,
(raw_payload ->> 'over_number')::int as over_number,
(raw_payload ->> 'ball_number')::int as ball_number,

-- Players
raw_payload ->> 'batter' as batter,
raw_payload ->> 'bowler' as bowler,
raw_payload ->> 'non_striker' as non_striker,
raw_payload ->> 'batter_id' as batter_id,
raw_payload ->> 'bowler_id' as bowler_id,

-- Runs
(raw_payload ->> 'batter_runs')::int as batter_runs,
(raw_payload ->> 'extra_runs')::int as extra_runs,
(raw_payload ->> 'total_runs')::int as total_runs,
raw_payload ->> 'extras_type' as extras_type,

-- Wicket
(raw_payload ->> 'is_wicket')::boolean as is_wicket,
raw_payload ->> 'wicket_kind' as wicket_kind,
raw_payload ->> 'wicket_player_out' as wicket_player_out,
raw_payload -> 'wicket_fielders' as wicket_fielders,

-- Outcome
raw_payload ->> 'match_winner' as match_winner,
raw_payload ->> 'win_margin' as win_margin,

-- Metadata
ingested_at, kafka_offset from source )

select
    *,
    -- Generate unique delivery ID
    match_id || '_' || innings_number || '_' || over_number || '_' || ball_number as delivery_id,

-- Calculate legal ball indicator
case
    when extras_type in ('wides', 'noballs') then false
    else true
end as is_legal_delivery
from flattened
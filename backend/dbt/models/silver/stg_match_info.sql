-- Staging Match Info
-- One row per match with aggregated metadata

{{
    config(
        materialized='table',
        schema='silver'
    )
}}


with deliveries as (
    select * from {{ ref('stg_deliveries') }}
),

match_summary as (
    select
        match_id,
        min(match_date) as match_date,
        min(season) as season,
        min(event_name) as event_name,
        min(venue) as venue,
        min(match_type) as match_type,
        min(gender) as gender,
        min(team_type) as team_type,
        min(toss_winner) as toss_winner,
        min(toss_decision) as toss_decision,
        min(match_winner) as match_winner,
        min(win_margin) as win_margin,

-- Calculate total deliveries
count(*) as total_deliveries,

-- Calculate overs
max(case when innings_number = 1 then over_number + 1 else 0 end) as innings_1_overs,
        max(case when innings_number = 2 then over_number + 1 else 0 end) as innings_2_overs,

        min(ingested_at) as first_ingested_at,
        max(ingested_at) as last_ingested_at

    from deliveries
    group by match_id
),

with_teams as (
    select
        ms.*,

-- Extract teams from first delivery of match
d.teams_array ->> 0 as team_1, d.teams_array ->> 1 as team_2,

-- First innings batting team
first_value(d.batting_team) over (
            partition by ms.match_id
            order by d.innings_number, d.over_number, d.ball_number
        ) as first_innings_team

    from match_summary ms
    join deliveries d on ms.match_id = d.match_id
    qualify row_number() over (partition by ms.match_id order by d.innings_number, d.over_number, d.ball_number) = 1
)

select
    match_id,
    match_date::date as match_date,
    season,
    event_name,
    venue,
    match_type,
    gender,
    team_type,
    team_1,
    team_2,
    toss_winner,
    toss_decision,
    first_innings_team,
    match_winner,
    win_margin,

-- Derived fields
case
    when match_winner = team_1 then team_1
    when match_winner = team_2 then team_2
    else null
end as winner,
case
    when match_winner = first_innings_team then true
    else false
end as first_innings_team_won,
total_deliveries,
innings_1_overs,
innings_2_overs,
first_ingested_at,
last_ingested_at
from with_teams
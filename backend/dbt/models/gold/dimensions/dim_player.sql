-- Dimension: Player
-- One row per unique player with descriptive attributes
-- SCD Type 2 managed via dbt snapshots for role/team changes

{{
    config(
        materialized='table',
        schema='gold'
    )
}}


with player_data as (
    select distinct
        batter as player_name,
        batter_id as player_id,
        batting_team as national_team
    from {{ ref('stg_deliveries') }}
    where batter is not null

    union

    select distinct
        bowler as player_name,
        bowler_id as player_id,
        bowling_team as national_team
    from {{ ref('stg_deliveries') }}
    where bowler is not null
),

-- Deduplicate: prefer the record with a non-null player_id
deduplicated as (
    select
        player_name,
        max(player_id) as player_id,
        -- Use the most frequent team association
        mode() within group (order by national_team) as national_team
    from player_data
    group by player_name
),

-- Calculate player statistics for classification
player_stats as (
    select
        d.batter as player_name,
        count(*) as balls_faced,
        sum(d.batter_runs) as total_runs,
        case
            when count(*) > 0 then round(sum(d.batter_runs)::numeric / count(*) * 100, 2)
            else 0
        end as strike_rate
    from {{ ref('stg_deliveries') }} d
    group by d.batter
),

bowler_stats as (
    select
        d.bowler as player_name,
        count(case when d.is_legal_delivery then 1 end) as balls_bowled,
        sum(d.total_runs) as runs_conceded,
        sum(case when d.is_wicket then 1 else 0 end) as wickets_taken,
        case
            when count(case when d.is_legal_delivery then 1 end) > 0
            then round(
                sum(d.total_runs)::numeric /
                (count(case when d.is_legal_delivery then 1 end)::numeric / 6),
                2
            )
            else 0
        end as economy_rate
    from {{ ref('stg_deliveries') }} d
    group by d.bowler
)

select
    -- Surrogate key
    {{ dbt_utils.generate_surrogate_key(['dd.player_name']) }} as player_sk,

    -- Natural key
    dd.player_id,
    dd.player_name,

    -- Team
    dd.national_team,

    -- Batting stats summary
    coalesce(ps.balls_faced, 0) as total_balls_faced,
    coalesce(ps.total_runs, 0) as total_runs_scored,
    coalesce(ps.strike_rate, 0) as career_strike_rate,

    -- Bowling stats summary
    coalesce(bs.balls_bowled, 0) as total_balls_bowled,
    coalesce(bs.runs_conceded, 0) as total_runs_conceded,
    coalesce(bs.wickets_taken, 0) as total_wickets_taken,
    coalesce(bs.economy_rate, 0) as career_economy_rate,

    -- Player role classification
    case
        when coalesce(ps.balls_faced, 0) > 100 and coalesce(bs.balls_bowled, 0) > 100 then 'All-Rounder'
        when coalesce(ps.balls_faced, 0) > 100 then 'Batter'
        when coalesce(bs.balls_bowled, 0) > 100 then 'Bowler'
        else 'Unknown'
    end as player_role,

    -- Record metadata
    current_timestamp as loaded_at

from deduplicated dd
left join player_stats ps on dd.player_name = ps.player_name
left join bowler_stats bs on dd.player_name = bs.player_name

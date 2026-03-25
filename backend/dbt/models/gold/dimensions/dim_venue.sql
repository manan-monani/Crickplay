-- Dimension: Venue
-- One row per unique venue with geographic and pitch-specific data

{{
    config(
        materialized='table',
        schema='gold'
    )
}}


with venue_data as (
    select distinct
        venue
    from {{ ref('stg_match_info') }}
    where venue is not null and venue != 'unknown'
),

-- Calculate venue-level aggregated statistics
venue_stats as (
    select
        mi.venue,
        count(distinct mi.match_id) as matches_played,

        -- Average first innings score
        round(avg(
            case when d.innings_number = 1
            then d.total_runs else null end
        )::numeric, 2) as avg_run_per_delivery,

        -- Wickets per match
        round(avg(
            case when d.is_wicket then 1 else 0 end
        )::numeric * 100, 2) as wicket_percentage,

        -- Boundary percentage
        round(
            sum(case when d.batter_runs in (4, 6) then 1 else 0 end)::numeric /
            nullif(count(*), 0) * 100,
            2
        ) as boundary_percentage,

        -- Dot ball percentage
        round(
            sum(case when d.total_runs = 0 then 1 else 0 end)::numeric /
            nullif(count(*), 0) * 100,
            2
        ) as dot_ball_percentage

    from {{ ref('stg_match_info') }} mi
    join {{ ref('stg_deliveries') }} d on mi.match_id = d.match_id
    group by mi.venue
),

-- Calculate first innings totals per match for average score
first_innings_scores as (
    select
        mi.venue,
        mi.match_id,
        sum(d.total_runs) as first_innings_total
    from {{ ref('stg_match_info') }} mi
    join {{ ref('stg_deliveries') }} d
        on mi.match_id = d.match_id
        and d.innings_number = 1
    group by mi.venue, mi.match_id
),

venue_avg_scores as (
    select
        venue,
        round(avg(first_innings_total)::numeric, 0) as avg_first_innings_score,
        round(min(first_innings_total)::numeric, 0) as min_first_innings_score,
        round(max(first_innings_total)::numeric, 0) as max_first_innings_score
    from first_innings_scores
    group by venue
),

-- Toss impact: what % of toss winners also win the match
toss_impact as (
    select
        venue,
        count(*) as total_matches_with_toss,
        sum(case when toss_winner = match_winner then 1 else 0 end) as toss_winner_match_winner,
        round(
            sum(case when toss_winner = match_winner then 1 else 0 end)::numeric /
            nullif(count(*), 0) * 100,
            2
        ) as toss_win_match_win_pct
    from {{ ref('stg_match_info') }}
    where match_winner is not null
    group by venue
),

-- Chase success rate at venue
chase_success as (
    select
        venue,
        count(*) as total_chases,
        sum(case when first_innings_team_won = false then 1 else 0 end) as chases_won,
        round(
            sum(case when first_innings_team_won = false then 1 else 0 end)::numeric /
            nullif(count(*), 0) * 100,
            2
        ) as chase_success_rate
    from {{ ref('stg_match_info') }}
    where match_winner is not null
    group by venue
)

select
    -- Surrogate key
    {{ dbt_utils.generate_surrogate_key(['vd.venue']) }} as venue_sk,

    -- Venue info
    vd.venue as stadium_name,

    -- Aggregated stats
    coalesce(vs.matches_played, 0) as matches_played,
    coalesce(vas.avg_first_innings_score, 0) as avg_first_innings_score,
    coalesce(vas.min_first_innings_score, 0) as min_first_innings_score,
    coalesce(vas.max_first_innings_score, 0) as max_first_innings_score,
    coalesce(vs.boundary_percentage, 0) as boundary_percentage,
    coalesce(vs.dot_ball_percentage, 0) as dot_ball_percentage,
    coalesce(vs.wicket_percentage, 0) as wicket_percentage,

    -- Toss and chase metrics
    coalesce(ti.toss_win_match_win_pct, 0) as toss_impact_pct,
    coalesce(cs.chase_success_rate, 0) as chase_success_rate,

    -- Pitch type classification (heuristic)
    case
        when coalesce(vas.avg_first_innings_score, 0) >= 170 then 'Batting'
        when coalesce(vs.wicket_percentage, 0) >= 5.0 then 'Bowling'
        when coalesce(vs.dot_ball_percentage, 0) >= 40.0 then 'Spin-friendly'
        else 'Balanced'
    end as pitch_type,

    -- Record metadata
    current_timestamp as loaded_at

from venue_data vd
left join venue_stats vs on vd.venue = vs.venue
left join venue_avg_scores vas on vd.venue = vas.venue
left join toss_impact ti on vd.venue = ti.venue
left join chase_success cs on vd.venue = cs.venue

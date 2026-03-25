-- Fact: Match Summary
-- One row per match — aggregated from fact_delivery
-- Contains match-level outcomes and aggregated statistics

{{
    config(
        materialized='table',
        schema='gold'
    )
}}


with match_deliveries as (
    select * from {{ ref('fact_delivery') }}
),

-- Aggregate per match per innings
innings_agg as (
    select
        match_id,
        innings_number,
        batting_team,
        bowling_team,

        -- Score totals
        sum(total_runs) as innings_total_runs,
        sum(batter_runs) as innings_batter_runs,
        sum(extra_runs) as innings_extras,

        -- Wickets
        sum(case when is_wicket then 1 else 0 end) as innings_wickets,

        -- Boundaries
        sum(case when is_four then 1 else 0 end) as innings_fours,
        sum(case when is_six then 1 else 0 end) as innings_sixes,

        -- Dot balls
        sum(case when is_dot_ball then 1 else 0 end) as innings_dot_balls,

        -- Delivery counts
        count(*) as total_deliveries,
        sum(case when is_legal_delivery then 1 else 0 end) as legal_deliveries,

        -- Overs bowled (legal deliveries / 6)
        round(
            sum(case when is_legal_delivery then 1 else 0 end)::numeric / 6,
            1
        ) as overs_bowled,

        -- Run rate
        case
            when sum(case when is_legal_delivery then 1 else 0 end) > 0
            then round(
                sum(total_runs)::numeric /
                (sum(case when is_legal_delivery then 1 else 0 end)::numeric / 6),
                2
            )
            else 0
        end as run_rate

    from match_deliveries
    group by match_id, innings_number, batting_team, bowling_team
),

-- Pivot innings into match summary
match_summary as (
    select
        i1.match_id,

        -- First innings
        i1.batting_team as team_batting_first,
        i1.bowling_team as team_batting_second,
        i1.innings_total_runs as first_innings_total,
        i1.innings_wickets as first_innings_wickets,
        i1.overs_bowled as first_innings_overs,
        i1.run_rate as first_innings_run_rate,
        i1.innings_fours as first_innings_fours,
        i1.innings_sixes as first_innings_sixes,
        i1.innings_dot_balls as first_innings_dot_balls,

        -- Second innings
        coalesce(i2.innings_total_runs, 0) as second_innings_total,
        coalesce(i2.innings_wickets, 0) as second_innings_wickets,
        coalesce(i2.overs_bowled, 0) as second_innings_overs,
        coalesce(i2.run_rate, 0) as second_innings_run_rate,
        coalesce(i2.innings_fours, 0) as second_innings_fours,
        coalesce(i2.innings_sixes, 0) as second_innings_sixes,
        coalesce(i2.innings_dot_balls, 0) as second_innings_dot_balls

    from innings_agg i1
    left join innings_agg i2
        on i1.match_id = i2.match_id
        and i2.innings_number = 2
    where i1.innings_number = 1
),

-- Join with match context for outcome
final as (
    select
        -- Surrogate key
        {{ dbt_utils.generate_surrogate_key(['ms.match_id']) }} as match_summary_sk,

        -- Natural key
        ms.match_id,

        -- Context dimension
        mc.match_context_sk,
        mc.match_date,
        mc.season,
        mc.venue,
        mc.event_name,
        mc.tournament_phase,
        mc.is_knockout,

        -- Teams
        ms.team_batting_first,
        ms.team_batting_second,

        -- Toss
        mc.toss_winner,
        mc.toss_decision,
        mc.toss_winner_won_match,

        -- First innings stats
        ms.first_innings_total,
        ms.first_innings_wickets,
        ms.first_innings_overs,
        ms.first_innings_run_rate,
        ms.first_innings_fours,
        ms.first_innings_sixes,
        ms.first_innings_dot_balls,

        -- Second innings stats
        ms.second_innings_total,
        ms.second_innings_wickets,
        ms.second_innings_overs,
        ms.second_innings_run_rate,
        ms.second_innings_fours,
        ms.second_innings_sixes,
        ms.second_innings_dot_balls,

        -- Combined stats
        ms.first_innings_total + ms.second_innings_total as total_match_runs,
        ms.first_innings_fours + ms.second_innings_fours as total_fours,
        ms.first_innings_sixes + ms.second_innings_sixes as total_sixes,

        -- Outcome
        mc.match_winner,
        mc.win_margin,
        mc.first_innings_team_won,

        -- Margin calculation
        case
            when mc.first_innings_team_won then
                ms.first_innings_total - ms.second_innings_total
            else
                0
        end as margin_runs,

        case
            when mc.first_innings_team_won = false then
                10 - ms.second_innings_wickets
            else
                0
        end as margin_wickets,

        -- Multi-tenancy
        'default' as tenant_id,

        -- Metadata
        current_timestamp as loaded_at

    from match_summary ms
    join {{ ref('dim_match_context') }} mc
        on ms.match_id = mc.match_id
)

select * from final

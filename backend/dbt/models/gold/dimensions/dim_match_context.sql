-- Dimension: Match Context
-- Contextual and environmental data for each match
-- Covers toss, tournament phase, match conditions

{{
    config(
        materialized='table',
        schema='gold'
    )
}}


with match_data as (
    select
        match_id,
        match_date,
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
        first_innings_team_won
    from {{ ref('stg_match_info') }}
),

-- Determine tournament phase from event name
enriched as (
    select
        *,

        -- Tournament phase classification
        case
            when lower(event_name) like '%final%' and lower(event_name) not like '%semi%' then 'Final'
            when lower(event_name) like '%semi%' then 'Semi-final'
            when lower(event_name) like '%qualifier%' or lower(event_name) like '%eliminator%' then 'Knockout'
            when lower(event_name) like '%super%' then 'Super Stage'
            else 'Group Stage'
        end as tournament_phase,

        -- Toss decision context
        case
            when toss_decision = 'bat' then 'Bat First'
            when toss_decision = 'field' then 'Field First'
            else 'Unknown'
        end as toss_decision_label,

        -- Did the toss winner also win?
        case
            when toss_winner = match_winner then true
            else false
        end as toss_winner_won_match,

        -- Is knockout match?
        case
            when lower(event_name) like '%final%'
                or lower(event_name) like '%semi%'
                or lower(event_name) like '%qualifier%'
                or lower(event_name) like '%eliminator%'
            then true
            else false
        end as is_knockout

    from match_data
)

select
    -- Surrogate key
    {{ dbt_utils.generate_surrogate_key(['match_id']) }} as match_context_sk,

    -- Natural key
    match_id,

    -- Match identification
    match_date,
    season,
    event_name,
    venue,
    match_type,
    gender,
    team_type,

    -- Teams
    team_1,
    team_2,
    first_innings_team,

    -- Toss info
    toss_winner,
    toss_decision,
    toss_decision_label,
    toss_winner_won_match,

    -- Tournament context
    tournament_phase,
    is_knockout,

    -- Outcome
    match_winner,
    win_margin,
    first_innings_team_won,

    -- Record metadata
    current_timestamp as loaded_at

from enriched

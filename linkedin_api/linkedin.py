"""
Provides linkedin api-related code
"""
import base64
from http.client import HTTPException
import json
import logging
import random
import uuid
from operator import itemgetter
from time import sleep, time
from urllib.parse import quote, urlencode

import requests

from .client import Client, UnauthorizedException
from .utils.helpers import (
    append_update_post_field_to_posts_list,
    get_id_from_urn,
    get_urn_from_raw_update,
    get_list_posts_sorted_without_promoted,
    get_update_author_name,
    get_update_author_profile,
    get_update_content,
    get_update_old,
    get_update_url,
    parse_list_raw_posts,
    parse_list_raw_urns,
    generate_trackingId,
    generate_trackingId_as_charString,
    get_nested
)

logger = logging.getLogger(__name__)


def default_evade():
    """
    A catch-all method to try and evade suspension from Linkedin.
    Currenly, just delays the request by a random (bounded) time
    """
    sleep(random.randint(2, 4))  # sleep a random duration to try and evade suspention


class Linkedin(object):
    """
    Class for accessing the LinkedIn API.

    :param username: Username of LinkedIn account.
    :type username: str
    :param password: Password of LinkedIn account.
    :type password: str
    """

    _MAX_POST_COUNT = 100  # max seems to be 100 posts per page
    _MAX_UPDATE_COUNT = 100  # max seems to be 100
    _MAX_SEARCH_COUNT = 49  # max seems to be 49, and min seems to be 2
    _MAX_REPEATED_REQUESTS = (
        200  # VERY conservative max requests count to avoid rate-limit
    )

    withoutEvade = False

    def __init__(
        self,
        username,
        password,
        *,
        authenticate=True,
        refresh_cookies=False,
        debug=False,
        proxies={},
        cookies=None,
        cookies_dir=None,
        withoutEvade=False
    ):
        """Constructor method"""
        self.client = Client(
            refresh_cookies=refresh_cookies,
            debug=debug,
            proxies=proxies,
            cookies_dir=cookies_dir,
        )
        logging.basicConfig(level=logging.DEBUG if debug else logging.INFO)
        self.logger = logger
        self.withoutEvade = withoutEvade

        if authenticate:
            if cookies:
                # If the cookies are expired, the API won't work anymore since
                # `username` and `password` are not used at all in this case.
                self.client._set_session_cookies(cookies)
            else:
                self.client.authenticate(username, password)

    def _evade(self):
        if(self.withoutEvade): return
        else: default_evade()

    def _fetch(self, uri, evade=None, base_request=False, **kwargs):
        """GET request to Linkedin API"""
        if(evade): evade()
        else: self._evade()

        url = f"{self.client.API_BASE_URL if not base_request else self.client.LINKEDIN_BASE_URL}{uri}"
        return self.client.session.get(url, **kwargs)

    def _post(self, uri, evade=None, base_request=False, **kwargs):
        """POST request to Linkedin API"""
        if(evade): evade()
        else: self._evade()

        url = f"{self.client.API_BASE_URL if not base_request else self.client.LINKEDIN_BASE_URL}{uri}"
        return self.client.session.post(url, **kwargs)

    def get_profile_posts(self, public_id=None, urn_id=None, post_count=10):
        """
        get_profile_posts: Get profile posts

        :param public_id: LinkedIn public ID for a profile
        :type public_id: str, optional
        :param urn_id: LinkedIn URN ID for a profile
        :type urn_id: str, optional
        :param post_count: Number of posts to fetch
        :type post_count: int, optional
        :return: List of posts
        :rtype: list
        """
        url_params = {
            "count": min(post_count, self._MAX_POST_COUNT),
            "start": 0,
            "q": "memberShareFeed",
            "moduleKey": "member-shares:phone",
            "includeLongTermHistory": True,
        }
        if urn_id:
            profile_urn = f"urn:li:fsd_profile:{urn_id}"
        else:
            profile = self.get_profile(public_id=public_id)
            profile_urn = profile["profile_urn"].replace(
                "fs_miniProfile", "fsd_profile"
            )
        url_params["profileUrn"] = profile_urn
        url = f"/identity/profileUpdatesV2"
        res = self._fetch(url, params=url_params)
        data = res.json()
        if data and "status" in data and data["status"] != 200:
            self.logger.info("request failed: {}".format(data["message"]))
            return {}
        while data and data["metadata"]["paginationToken"] != "":
            if len(data["elements"]) >= post_count:
                break
            pagination_token = data["metadata"]["paginationToken"]
            url_params["start"] = url_params["start"] + self._MAX_POST_COUNT
            url_params["paginationToken"] = pagination_token
            res = self._fetch(url, params=url_params)
            data["metadata"] = res.json()["metadata"]
            data["elements"] = data["elements"] + res.json()["elements"]
            data["paging"] = res.json()["paging"]
        return data["elements"]

    def get_post_comments(self, post_urn, comment_count=100):
        """
        get_post_comments: Get post comments

        :param post_urn: Post URN
        :type post_urn: str
        :param comment_count: Number of comments to fetch
        :type comment_count: int, optional
        :return: List of post comments
        :rtype: list
        """
        url_params = {
            "count": min(comment_count, self._MAX_POST_COUNT),
            "start": 0,
            "q": "comments",
            "sortOrder": "RELEVANCE",
        }
        url = f"/feed/comments"
        url_params["updateId"] = "activity:" + post_urn
        res = self._fetch(url, params=url_params)
        data = res.json()
        if data and "status" in data and data["status"] != 200:
            self.logger.info("request failed: {}".format(data["status"]))
            return {}
        while data and data["metadata"]["paginationToken"] != "":
            if len(data["elements"]) >= comment_count:
                break
            pagination_token = data["metadata"]["paginationToken"]
            url_params["start"] = url_params["start"] + self._MAX_POST_COUNT
            url_params["count"] = self._MAX_POST_COUNT
            url_params["paginationToken"] = pagination_token
            res = self._fetch(url, params=url_params)
            if res.json() and "status" in res.json() and res.json()["status"] != 200:
                self.logger.info("request failed: {}".format(data["status"]))
                return {}
            data["metadata"] = res.json()["metadata"]
            """ When the number of comments exceed total available 
            comments, the api starts returning an empty list of elements"""
            if res.json()["elements"] and len(res.json()["elements"]) == 0:
                break
            if data["elements"] and len(res.json()["elements"]) == 0:
                break
            data["elements"] = data["elements"] + res.json()["elements"]
            data["paging"] = res.json()["paging"]
        return data["elements"]
    
    def search(self, params, limit=-1, offset=0):
        """Perform a LinkedIn search.

        :param params: Search parameters (see code)
        :type params: dict
        :param limit: Maximum length of the returned list, defaults to -1 (no limit)
        :type limit: int, optional
        :param offset: Index to start searching from
        :type offset: int, optional


        :return: List of search results
        :rtype: list
        """
        count = Linkedin._MAX_SEARCH_COUNT
        if limit is None:
            limit = -1

        results = []
        while True:
            # when we're close to the limit, only fetch what we need to
            if limit > -1 and limit - len(results) < count:
                count = limit - len(results)
            default_params = {
                "count": str(count),
                "filters": "List()",
                "origin": "GLOBAL_SEARCH_HEADER",
                "q": "all",
                "start": len(results) + offset,
                "queryContext": "List(spellCorrectionEnabled->true,relatedSearchesEnabled->true,kcardTypes->PROFILE|COMPANY)",
            }
            default_params.update(params)

            keywords = (
                f"keywords:{default_params['keywords']},"
                if "keywords" in default_params
                else ""
            )

            try:
                res = self._fetch(
                    f"/graphql?variables=(start:{default_params['start']},origin:{default_params['origin']},"
                    f"query:("
                    f"{keywords}"
                    f"flagshipSearchIntent:SEARCH_SRP,"
                    f"queryParameters:{default_params['filters']},"
                    f"includeFiltersInResponse:false))&=&queryId=voyagerSearchDashClusters"
                    f".b0928897b71bd00a5a7291755dcd64f0"
                )
                res.raise_for_status()
            except requests.exceptions.HTTPError as error:
                print(f"HTTP error occurred: {error}")
                if error.response.status_code == 401:
                    return res.json()
            # except Exception as err:
            #     print(f"Other error occurred: {err}")
            #     return []
            
            data = res.json()

            
            data_clusters = data.get("data", []).get("searchDashClustersByAll", [])

            if not data_clusters:
                return []

            if (
                not data_clusters.get("_type", [])
                == "com.linkedin.restli.common.CollectionResponse"
            ):
                return []

            new_elements = []
            for it in data_clusters.get("elements", []):
                if (
                    not it.get("_type", [])
                    == "com.linkedin.voyager.dash.search.SearchClusterViewModel"
                ):
                    continue

                for el in it.get("items", []):
                    if (
                        not el.get("_type", [])
                        == "com.linkedin.voyager.dash.search.SearchItem"
                    ):
                        continue

                    e = el.get("item", []).get("entityResult", [])
                    if not e:
                        continue
                    if (
                        not e.get("_type", [])
                        == "com.linkedin.voyager.dash.search.EntityResultViewModel"
                    ):
                        continue
                    new_elements.append(e)

            results.extend(new_elements)

            # break the loop if we're done searching
            # NOTE: we could also check for the `total` returned in the response.
            # This is in data["data"]["paging"]["total"]
            if (
                (-1 < limit <= len(results))  # if our results exceed set limit
                or len(results) / count >= Linkedin._MAX_REPEATED_REQUESTS
            ) or len(new_elements) == 0:
                break

            self.logger.debug(f"results grew to {len(results)}")

        return results


    def search_people(
        self,
        keywords=None,
        connection_of=None,
        network_depths=None,
        current_company=None,
        past_companies=None,
        nonprofit_interests=None,
        profile_languages=None,
        regions=None,
        industries=None,
        schools=None,
        contact_interests=None,
        service_categories=None,
        include_private_profiles=False,  # profiles without a public id, "Linkedin Member"
        # Keywords filter
        keyword_first_name=None,
        keyword_last_name=None,
        # `keyword_title` and `title` are the same. We kept `title` for backward compatibility. Please only use one of them.
        keyword_title=None,
        keyword_company=None,
        keyword_school=None,
        network_depth=None,  # DEPRECATED - use network_depths
        title=None,  # DEPRECATED - use keyword_title
        **kwargs,
    ):
        """Perform a LinkedIn search for people.

        :param keywords: Keywords to search on
        :type keywords: str, optional
        :param current_company: A list of company URN IDs (str)
        :type current_company: list, optional
        :param past_companies: A list of company URN IDs (str)
        :type past_companies: list, optional
        :param regions: A list of geo URN IDs (str)
        :type regions: list, optional
        :param industries: A list of industry URN IDs (str)
        :type industries: list, optional
        :param schools: A list of school URN IDs (str)
        :type schools: list, optional
        :param profile_languages: A list of 2-letter language codes (str)
        :type profile_languages: list, optional
        :param contact_interests: A list containing one or both of "proBono" and "boardMember"
        :type contact_interests: list, optional
        :param service_categories: A list of service category URN IDs (str)
        :type service_categories: list, optional
        :param network_depth: Deprecated, use `network_depths`. One of "F", "S" and "O" (first, second and third+ respectively)
        :type network_depth: str, optional
        :param network_depths: A list containing one or many of "F", "S" and "O" (first, second and third+ respectively)
        :type network_depths: list, optional
        :param include_private_profiles: Include private profiles in search results. If False, only public profiles are included. Defaults to False
        :type include_private_profiles: boolean, optional
        :param keyword_first_name: First name
        :type keyword_first_name: str, optional
        :param keyword_last_name: Last name
        :type keyword_last_name: str, optional
        :param keyword_title: Job title
        :type keyword_title: str, optional
        :param keyword_company: Company name
        :type keyword_company: str, optional
        :param keyword_school: School name
        :type keyword_school: str, optional
        :param connection_of: Connection of LinkedIn user, given by profile URN ID
        :type connection_of: str, optional

        :return: List of profiles (minimal data only)
        :rtype: list
        """
        filters = ["(key:resultType,value:List(PEOPLE))"]
        if connection_of:
            filters.append(f"(key:connectionOf,value:List({connection_of}))")
        if network_depths:
            stringify = " | ".join(network_depths)
            filters.append(f"(key:network,value:List({stringify}))")
        elif network_depth:
            filters.append(f"(key:network,value:List({network_depth}))")
        if regions:
            stringify = " | ".join(regions)
            filters.append(f"(key:geoUrn,value:List({stringify}))")
        if industries:
            stringify = " | ".join(industries)
            filters.append(f"(key:industry,value:List({stringify}))")
        if current_company:
            stringify = " | ".join(current_company)
            filters.append(f"(key:currentCompany,value:List({stringify}))")
        if past_companies:
            stringify = " | ".join(past_companies)
            filters.append(f"(key:pastCompany,value:List({stringify}))")
        if profile_languages:
            stringify = " | ".join(profile_languages)
            filters.append(f"(key:profileLanguage,value:List({stringify}))")
        if nonprofit_interests:
            stringify = " | ".join(nonprofit_interests)
            filters.append(f"(key:nonprofitInterest,value:List({stringify}))")
        if schools:
            stringify = " | ".join(schools)
            filters.append(f"(key:schools,value:List({stringify}))")
        if service_categories:
            stringify = " | ".join(service_categories)
            filters.append(f"(key:serviceCategory,value:List({stringify}))")
        # `Keywords` filter
        keyword_title = keyword_title if keyword_title else title
        if keyword_first_name:
            filters.append(f"(key:firstName,value:List({keyword_first_name}))")
        if keyword_last_name:
            filters.append(f"(key:lastName,value:List({keyword_last_name}))")
        if keyword_title:
            filters.append(f"(key:title,value:List({keyword_title}))")
        if keyword_company:
            filters.append(f"(key:company,value:List({keyword_company}))")
        if keyword_school:
            filters.append(f"(key:school,value:List({keyword_school}))")

        params = {"filters": "List({})".format(",".join(filters))}

        if keywords:
            params["keywords"] = keywords

        data = self.search(params, **kwargs)

        results = []
        for item in data:
            if (
                not include_private_profiles
                and (item.get("entityCustomTrackingInfo") or {}).get(
                    "memberDistance", None
                )
                == "OUT_OF_NETWORK"
            ):
                continue
            results.append(
                {
                    "urn_id": get_id_from_urn(
                        get_urn_from_raw_update(item.get("entityUrn", None))
                    ),
                    "distance": (item.get("entityCustomTrackingInfo") or {}).get(
                        "memberDistance", None
                    ),
                    "jobtitle": (item.get("primarySubtitle") or {}).get("text", None),
                    "location": (item.get("secondarySubtitle") or {}).get("text", None),
                    "name": (item.get("title") or {}).get("text", None),
                }
            )

        return results

    def search_companies(self, keywords=None, **kwargs):
        """Perform a LinkedIn search for companies.

        :param keywords: A list of search keywords (str)
        :type keywords: list, optional

        :return: List of companies
        :rtype: list
        """
        filters = ["(key:resultType,value:List(COMPANIES))"]

        params = {
            "filters": "List({})".format(",".join(filters)),
            "queryContext": "List(spellCorrectionEnabled->true)",
        }

        if keywords:
            params["keywords"] = keywords

        data = self.search(params, **kwargs)

        results = []
        for item in data:
            if "company" not in item.get("trackingUrn"):
                continue
            results.append(
                {
                    "urn_id": get_id_from_urn(item.get("trackingUrn", None)),
                    "name": (item.get("title") or {}).get("text", None),
                    "headline": (item.get("primarySubtitle") or {}).get("text", None),
                    "subline": (item.get("secondarySubtitle") or {}).get("text", None),
                }
            )

        return results

    def search_jobs(
        self,
        keywords=None,
        companies=None,
        experience=None,
        job_type=None,
        job_title=None,
        industries=None,
        location_name=None,
        remote=None,
        listed_at=24 * 60 * 60,
        distance=None,
        limit=-1,
        offset=0,
        **kwargs,
    ):
        """Perform a LinkedIn search for jobs.

        :param keywords: Search keywords (str)
        :type keywords: str, optional
        :param companies: A list of company URN IDs (str)
        :type companies: list, optional
        :param experience: A list of experience levels, one or many of "1", "2", "3", "4", "5" and "6" (internship, entry level, associate, mid-senior level, director and executive, respectively)
        :type experience: list, optional
        :param job_type:  A list of job types , one or many of "F", "C", "P", "T", "I", "V", "O" (full-time, contract, part-time, temporary, internship, volunteer and "other", respectively)
        :type job_type: list, optional
        :param job_title: A list of title URN IDs (str)
        :type job_title: list, optional
        :param industries: A list of industry URN IDs (str)
        :type industries: list, optional
        :param location_name: Name of the location to search within. Example: "Kyiv City, Ukraine"
        :type location_name: str, optional
        :param remote: Filter for remote jobs, onsite or hybrid. onsite:"1", remote:"2", hybrid:"3"
        :type remote: list, optional
        :param listed_at: maximum number of seconds passed since job posting. 86400 will filter job postings posted in last 24 hours.
        :type listed_at: int/str, optional. Default value is equal to 24 hours.
        :param distance: maximum distance from location in miles
        :type distance: int/str, optional. If not specified, None or 0, the default value of 25 miles applied.
        :param limit: maximum number of results obtained from API queries. -1 means maximum which is defined by constants and is equal to 1000 now.
        :type limit: int, optional, default -1
        :param offset: indicates how many search results shall be skipped
        :type offset: int, optional
        :return: List of jobs
        :rtype: list
        """
        count = Linkedin._MAX_SEARCH_COUNT
        if limit is None:
            limit = -1

        query = {"origin":"JOB_SEARCH_PAGE_QUERY_EXPANSION"}
        if keywords:
            query["keywords"] = "KEYWORD_PLACEHOLDER"
        if location_name:
            query["locationFallback"] = "LOCATION_PLACEHOLDER"

        # In selectedFilters()
        query['selectedFilters'] = {}
        if companies:
            query['selectedFilters']['company'] = f"List({','.join(companies)})"
        if experience:
            query['selectedFilters']['experience'] = f"List({','.join(experience)})"
        if job_type:
            query['selectedFilters']['jobType'] = f"List({','.join(job_type)})"
        if job_title:
            query['selectedFilters']['title'] = f"List({','.join(job_title)})"
        if industries:
            query['selectedFilters']['industry'] = f"List({','.join(industries)})"
        if distance:
            query['selectedFilters']['distance'] = f"List({distance})"
        if remote:
            query['selectedFilters']['workplaceType'] = f"List({','.join(remote)})"

        query['selectedFilters']['timePostedRange'] = f"List(r{listed_at})"
        query["spellCorrectionEnabled"] = "true"

        # Query structure:
        # "(
        #    origin:JOB_SEARCH_PAGE_QUERY_EXPANSION,
        #    keywords:marketing%20manager,
        #    locationFallback:germany,
        #    selectedFilters:(
        #        distance:List(25),
        #        company:List(163253),
        #        salaryBucketV2:List(5),
        #        timePostedRange:List(r2592000),
        #        workplaceType:List(1)
        #    ),
        #    spellCorrectionEnabled:true
        #  )"

        query = str(query).replace(" ","") \
                    .replace("'","") \
                    .replace("KEYWORD_PLACEHOLDER", keywords or "") \
                    .replace("LOCATION_PLACEHOLDER", location_name or "") \
                    .replace("{","(") \
                    .replace("}",")")
        results = []
        while True:
            # when we're close to the limit, only fetch what we need to
            if limit > -1 and limit - len(results) < count:
                count = limit - len(results)
            default_params = {
                "decorationId": "com.linkedin.voyager.dash.deco.jobs.search.JobSearchCardsCollection-174",
                "count": count,
                "q": "jobSearch",
                "query": query,
                "start": len(results) + offset,
            }

            res = self._fetch(
                f"/voyagerJobsDashJobCards?{urlencode(default_params, safe='(),:')}",
                headers={"accept": "application/vnd.linkedin.normalized+json+2.1"},
            )
            data = res.json()

            elements = data.get("included", [])
            new_data = [
                i
                for i in elements
                if i["$type"] == 'com.linkedin.voyager.dash.jobs.JobPosting'
            ]
            # break the loop if we're done searching or no results returned
            if not new_data:
                break
            # NOTE: we could also check for the `total` returned in the response.
            # This is in data["data"]["paging"]["total"]
            results.extend(new_data)
            if (
                (-1 < limit <= len(results))  # if our results exceed set limit
                or len(results) / count >= Linkedin._MAX_REPEATED_REQUESTS
            ) or len(elements) == 0:
                break

            self.logger.debug(f"results grew to {len(results)}")

        return results

    def search_typeahead(self, keywords, search_type):
        """Perform a fuzzy typeahead search based on the provided keywords and search type.

        :param keywords: The search keywords
        :type keywords: str
        :param search_type: The type of search (e.g., GEO, COMPANY, SCHOOL, CONNECTIONS)
        :type search_type: str

        :return: List of search results
        :rtype: list
        """

        def _get_query_for_type():
            """Helper function to get the correct query parameter based on search type."""
            if search_type == "GEO":
                return "(typeaheadFilterQuery:(geoSearchTypes:List(MARKET_AREA,COUNTRY_REGION,ADMIN_DIVISION_1,CITY)))"
            if search_type == "SKILL":
                return "(typeaheadUseCase:MARKETPLACE)"
            else:
                return "()"

        # Construct the base URL and query parameters
        base_url = "/graphql"
        query_parameters = {
            "keywords": keywords,
            "query": _get_query_for_type(),
            "type": search_type
        }
        query_id = "voyagerSearchDashReusableTypeahead.f4b5dab74a7f77bb04289c36f40c7338"

        # Create the query string from the parameters
        query_string = f"variables=(keywords:{query_parameters['keywords']},query:{query_parameters['query']},type:{query_parameters['type']})&queryId={query_id}"
        
        # Construct the final URL
        full_url = f"{base_url}?{query_string}"

        # Define headers
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "application/vnd.linkedin.normalized+json+2.1",
            "X-RestLi-Protocol-Version": "2.0.0",
            "Content-Type": "application/json",
        }

        # Fetch the search results
        try:
            res = self._fetch(full_url, headers=headers)
            res.raise_for_status()  # Raise an exception for HTTP errors
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")
            return []
        except Exception as err:
            print(f"Other error occurred: {err}")
            return []

        # Attempt to parse JSON response
        try:
            data = res.json()
        except ValueError:
            print("Response is not in JSON format. Here is the raw response content:")
            print(res.text)
            return []

        # Safely access nested data
        search_data = data.get("data", {}).get("data", {}).get("searchDashReusableTypeaheadByType", {})
        elements = search_data.get("elements", [])

        # Set the flag to skip image URL retrieval for specific search types
        skip_image_url = search_type in ["GEO", "SKILL", "INDUSTRY"]

        search_results = []
        for element in elements:
            image_url = None
            profile_urn = None

            # Check for 'CONNECTIONS' type to grab the profile URN
            if search_type == "CONNECTIONS":
                detail_data = element.get("image", {}).get("attributes", [{}])[0].get("detailData", {})
                profile_data = detail_data.get("nonEntityProfilePicture", {})
                profile_urn = profile_data.get("*profile")
            
            # Ensure 'image' and 'attributes' are available
            if not skip_image_url:
                image_data = element.get("image", {}).get("attributes", [])
                if image_data is not None and isinstance(image_data, list) and len(image_data) > 0:
                    detail_data = image_data[0].get("detailData", {})
                    non_entity_logo = detail_data.get("nonEntityCompanyLogo") or detail_data.get("nonEntityProfilePicture", {})
                    vector_image = non_entity_logo.get("vectorImage") if non_entity_logo else None
                    
                    if vector_image:
                        root_url = vector_image.get("rootUrl", None)
                        file_segment = None
                        artifacts = vector_image.get("artifacts", [])
                        
                        if artifacts and isinstance(artifacts, list) and len(artifacts) > 0:
                            # Try to find the largest artifact (e.g., 400 width)
                            for artifact in artifacts:
                                if artifact.get("width") == 400:
                                    file_segment = artifact.get("fileIdentifyingUrlPathSegment")
                                    break
                            if not file_segment:
                                file_segment = artifacts[0].get("fileIdentifyingUrlPathSegment")
                        
                        if root_url and file_segment:
                            image_url = f"{root_url}{file_segment}"

            # Add the result to search_results
            search_result = {
                "title": element.get("title", {}).get("text", "No Title"),
                "objectUrn": element.get("trackingUrn", "No Urn"),
                "image_url": image_url
            }
            if search_type == "CONNECTIONS":
                search_result["urn_id"] = profile_urn or None
            search_results.append(search_result)

            # Return the search results
        return search_results


    def get_profile_contact_info(self, public_id=None, urn_id=None):
        """Fetch contact information for a given LinkedIn profile. Pass a [public_id] or a [urn_id].

        :param public_id: LinkedIn public ID for a profile
        :type public_id: str, optional
        :param urn_id: LinkedIn URN ID for a profile
        :type urn_id: str, optional

        :return: Contact data
        :rtype: dict
        """
        res = self._fetch(
            f"/identity/profiles/{public_id or urn_id}/profileContactInfo"
        )
        data = res.json()

        contact_info = {
            "email_address": data.get("emailAddress"),
            "websites": [],
            "twitter": data.get("twitterHandles"),
            "birthdate": data.get("birthDateOn"),
            "ims": data.get("ims"),
            "phone_numbers": data.get("phoneNumbers", []),
        }

        websites = data.get("websites", [])
        for item in websites:
            if "com.linkedin.voyager.identity.profile.StandardWebsite" in item["type"]:
                item["label"] = item["type"][
                    "com.linkedin.voyager.identity.profile.StandardWebsite"
                ]["category"]
            elif "" in item["type"]:
                item["label"] = item["type"][
                    "com.linkedin.voyager.identity.profile.CustomWebsite"
                ]["label"]

            del item["type"]

        contact_info["websites"] = websites

        return contact_info

    def get_profile_contact_info_graphql(self, public_id=None, urn_id=None, include_web_metadata=True):
        """Fetch contact information for a given LinkedIn profile using GraphQL API.

        :param public_id: LinkedIn public ID for a profile (e.g., 'johndinsmore1')
        :type public_id: str, optional
        :param urn_id: LinkedIn URN ID for a profile (will fetch public_id if provided)
        :type urn_id: str, optional
        :param include_web_metadata: Include web metadata in the response
        :type include_web_metadata: bool, optional

        :return: Contact data
        :rtype: dict
        """
        print(f"=== get_profile_contact_info_graphql called with public_id={public_id}, urn_id={urn_id} ===")
        
        # If urn_id is provided but not public_id, fetch the profile to get public_id
        if urn_id and not public_id:
            profile = self.get_profile(urn_id=urn_id)
            public_id = profile.get("public_id")
            if not public_id:
                raise ValueError(f"Could not retrieve public_id for urn_id: {urn_id}")
        
        if not public_id:
            raise ValueError("Either public_id or urn_id is required for get_profile_contact_info_graphql")

        # GraphQL query ID for profile contact info
        query_id = "voyagerIdentityDashProfiles.c7452e58fa37646d09dae4920fc5b4b9"
        
        # Build the variables string
        variables = f"(memberIdentity:{public_id})"
        
        # Construct the query string manually - LinkedIn expects it exactly as shown
        include_metadata = "true" if include_web_metadata else "false"
        query_string = f"includeWebMetadata={include_metadata}&variables={variables}&queryId={query_id}"
        full_url = f"/graphql?{query_string}"
        
        logger.info(f"Fetching contact info for public_id: {public_id}")
        logger.info(f"Full URL: {full_url}")
        
        # Generate a page instance ID for contact details page
        random_bytes = bytes([random.randint(0, 255) for _ in range(16)])
        page_instance_id = base64.b64encode(random_bytes).decode('utf-8').rstrip('=')
        page_instance = f"urn:li:page:d_flagship3_profile_view_base_contact_details;{page_instance_id}"
        
        # Add required headers for GraphQL endpoint
        headers = {
            "accept": "application/vnd.linkedin.normalized+json+2.1",
            "x-restli-protocol-version": "2.0.0",
            "referer": f"https://www.linkedin.com/in/{public_id}/",
            "x-li-page-instance": page_instance,
            "x-li-track": '{"clientVersion":"1.13.39992","mpVersion":"1.13.39992","osName":"web","timezoneOffset":-4,"timezone":"America/New_York","deviceFormFactor":"DESKTOP","mpName":"voyager-web","displayDensity":2,"displayWidth":6400,"displayHeight":2666}',
        }
        
        try:
            res = self._fetch(full_url, headers=headers)
            print(f"Response status: {res.status_code}")
            data = res.json()
            print(f"Response data keys: {data.keys()}")
        except Exception as e:
            print(f"!!! Error fetching contact info GraphQL: {e}")
            print(f"!!! URL: {full_url}")
            logger.error(f"Error fetching contact info GraphQL: {e}")
            logger.error(f"URL: {full_url}")
            raise
        
        # Debug: Log the response structure
        logger.debug(f"GraphQL contact info response keys: {data.keys()}")
        if "errors" in data:
            print(f"!!! GraphQL errors found: {data['errors']}")
            logger.error(f"GraphQL errors: {data['errors']}")
            raise Exception(f"GraphQL returned errors: {data['errors']}")
        
        # Parse the GraphQL response to extract contact info
        # The profile data is in the 'included' array with type Profile
        contact_info = {}
        
        included = data.get("included", [])
        logger.debug(f"Number of included items: {len(included)}")
        
        # Find the Profile object in the included array
        profile_data = None
        for item in included:
            if item.get("$type") == "com.linkedin.voyager.dash.identity.profile.Profile":
                profile_data = item
                break
        
        if profile_data:
            # Extract basic profile info
            first_name = profile_data.get("firstName")
            if first_name:
                contact_info["first_name"] = first_name
            
            last_name = profile_data.get("lastName")
            if last_name:
                contact_info["last_name"] = last_name
            
            public_identifier = profile_data.get("publicIdentifier")
            if public_identifier:
                contact_info["public_identifier"] = public_identifier
            
            headline = profile_data.get("headline")
            if headline:
                contact_info["headline"] = headline
            
            # Extract profile picture
            profile_picture = profile_data.get("profilePicture")
            if profile_picture:
                # Get the display image reference (without frame)
                display_image_ref = profile_picture.get("displayImageReferenceResolutionResult", {})
                vector_image = display_image_ref.get("vectorImage")
                
                if vector_image:
                    root_url = vector_image.get("rootUrl", "")
                    artifacts = vector_image.get("artifacts", [])
                    
                    # Build image URLs for different sizes
                    images = {}
                    for artifact in artifacts:
                        width = artifact.get("width")
                        file_segment = artifact.get("fileIdentifyingUrlPathSegment")
                        if width and file_segment:
                            images[f"{width}x{width}"] = f"{root_url}{file_segment}"
                    
                    if images:
                        contact_info["profile_picture"] = {
                            "root_url": root_url,
                            "images": images
                        }
            
            # Extract email
            email_obj = profile_data.get("emailAddress", {})
            if email_obj and isinstance(email_obj, dict):
                email = email_obj.get("emailAddress")
                if email:
                    contact_info["email_address"] = email
            
            # Extract websites
            websites = profile_data.get("websites", [])
            if websites:
                # Parse website objects to match JavaScript parser expectations
                parsed_websites = []
                for site in websites:
                    website_obj = {
                        "url": site.get("url"),
                        # JS parser expects 'type' or 'label', map category to type
                        "type": site.get("category") or site.get("label") or "OTHER",
                    }
                    # Also include label if present for backward compatibility
                    if site.get("label"):
                        website_obj["label"] = site.get("label")
                    parsed_websites.append(website_obj)
                contact_info["websites"] = parsed_websites
            
            # Extract twitter handles
            twitter_handles = profile_data.get("twitterHandles", [])
            if twitter_handles:
                # Parse to match JavaScript parser expectations (expects objects with 'name' property)
                parsed_twitter = []
                for handle in twitter_handles:
                    twitter_obj = {
                        "name": handle.get("name") or handle.get("credentialId")
                    }
                    if twitter_obj["name"]:
                        parsed_twitter.append(twitter_obj)
                if parsed_twitter:
                    contact_info["twitter"] = parsed_twitter
            
            # Extract birthdate
            birthdate = profile_data.get("birthDateOn")
            if birthdate:
                # Clean up birthdate - remove GraphQL metadata, keep only month and day
                contact_info["birthdate"] = {
                    "month": birthdate.get("month"),
                    "day": birthdate.get("day")
                }
            
            # Extract phone numbers
            phone_numbers = profile_data.get("phoneNumbers", [])
            if phone_numbers:
                # Parse phone number objects
                parsed_phones = []
                for phone in phone_numbers:
                    phone_obj = phone.get("phoneNumber", {})
                    if phone_obj:
                        parsed_phones.append({
                            "number": phone_obj.get("number"),
                            "type": phone.get("type")
                        })
                contact_info["phone_numbers"] = parsed_phones
            
            # Extract instant messengers
            ims = profile_data.get("instantMessengers", [])
            if ims:
                # Parse to match JavaScript parser expectations (expects 'provider' and 'name')
                parsed_ims = []
                for im in ims:
                    im_obj = {
                        "provider": im.get("provider"),
                        "name": im.get("id")  # LinkedIn uses 'id' field for the handle
                    }
                    if im_obj["provider"] and im_obj["name"]:
                        parsed_ims.append(im_obj)
                if parsed_ims:
                    contact_info["ims"] = parsed_ims
            
            # Extract address if present
            address = profile_data.get("address")
            if address:
                contact_info["address"] = address
        
        return contact_info

    def get_profile_skills(self, public_id=None, urn_id=None):
        """Fetch the skills listed on a given LinkedIn profile (LEGACY - kept for reference).

        :param public_id: LinkedIn public ID for a profile
        :type public_id: str, optional
        :param urn_id: LinkedIn URN ID for a profile
        :type urn_id: str, optional


        :return: List of skill objects
        :rtype: list
        """
        params = {"count": 100, "start": 0}
        res = self._fetch(
            f"/identity/profiles/{public_id or urn_id}/skills", params=params
        )
        data = res.json()

        skills = data.get("elements", [])
        for item in skills:
            del item["entityUrn"]

        return skills

    def get_profile_skills_graphql(self, urn_id=None, locale="en_US"):
        """Fetch the skills listed on a given LinkedIn profile using GraphQL API.

        :param urn_id: LinkedIn URN ID for a profile (e.g., 'ACoAAAZ_m9sBjNJI6ZqXy2dacAAipjGGjPQEAZY')
        :type urn_id: str
        :param locale: Locale for the response (default: en_US)
        :type locale: str, optional

        :return: Skills data from GraphQL response
        :rtype: dict
        """
        if not urn_id:
            raise ValueError("urn_id is required for get_profile_skills_graphql")

        # Construct the full profile URN - ensure it has the proper format
        if not urn_id.startswith("urn:li:fsd_profile:"):
            profile_urn = f"urn:li:fsd_profile:{urn_id}"
        else:
            profile_urn = urn_id
        
        # Build the variables string exactly as LinkedIn expects
        # Note: sectionType and locale appear to be string literals without quotes in the GraphQL query
        variables = f"(profileUrn:{profile_urn},sectionType:skills,locale:{locale})"
        
        # GraphQL query ID for profile components
        # Note: This queryId may need to be updated periodically as LinkedIn changes their API
        # The queryId can be found by inspecting network requests in the browser when viewing a profile's skills section
        query_id = "voyagerIdentityDashProfileComponents.c5d4db426a0f8247b8ab7bc1d660775a"
        
        # Try alternative query IDs if the primary one fails
        # These are common variations that LinkedIn uses
        alternative_query_ids = [
            "voyagerIdentityDashProfileComponents.c5d4db426a0f8247b8ab7bc1d660775a",
            "voyagerIdentityDashProfileComponents.d6d4db426a0f8247b8ab7bc1d660775a",
        ]
        
        # Construct the query string manually (like search_typeahead does)
        # This ensures proper URL encoding that LinkedIn expects
        # We need to URL-encode the URN colons but keep the parentheses and commas unencoded
        # Encode only the URN part (the colons need to be %3A)
        encoded_urn = profile_urn.replace(":", "%3A")
        encoded_variables = f"(profileUrn:{encoded_urn},sectionType:skills,locale:{locale})"
        query_string = f"variables={encoded_variables}&queryId={query_id}"
        full_url = f"/graphql?{query_string}"
        
        # Generate a page instance ID (LinkedIn uses this to track page context)
        # Format: urn:li:page:d_flagship3_profile_view_base_skills_details;{random_id}
        random_bytes = bytes([random.randint(0, 255) for _ in range(16)])
        page_instance_id = base64.b64encode(random_bytes).decode('utf-8').rstrip('=')
        page_instance = f"urn:li:page:d_flagship3_profile_view_base_skills_details;{page_instance_id}"
        
        # Add required headers for GraphQL endpoint
        headers = {
            "accept": "application/vnd.linkedin.normalized+json+2.1",
            "x-restli-protocol-version": "2.0.0",
            "referer": f"https://www.linkedin.com/in/{urn_id}/details/skills/",
            "x-li-page-instance": page_instance,
            "x-li-pem-metadata": "Voyager - Profile=view-skills-details",
            "x-li-track": '{"clientVersion":"1.13.39992","mpVersion":"1.13.39992","osName":"web","timezoneOffset":-4,"timezone":"America/New_York","deviceFormFactor":"DESKTOP","mpName":"voyager-web","displayDensity":2,"displayWidth":6400,"displayHeight":2666}',
        }
        
        res = self._fetch(full_url, headers=headers)
        data = res.json()
        
        # Parse the GraphQL response to extract skills in a format similar to the legacy endpoint
        skills = []
        
        # The skills data is in the 'included' array
        included = data.get("included", [])
        
        # First, build a map of entityUrn to endorsement data from EndorsedSkill objects
        endorsed_skills_map = {}
        for item in included:
            if item.get("$type") == "com.linkedin.voyager.dash.identity.profile.EndorsedSkill":
                entity_urn = item.get("entityUrn")
                if entity_urn:
                    endorsed_skills_map[entity_urn] = {
                        "endorsementCount": item.get("endorsementCount", 0),
                        "endorsedByViewer": item.get("endorsedByViewer", False)
                    }
        
        # Now extract skills from PagedListComponent
        for item in included:
            # Look for PagedListComponent items which contain the skills
            if item.get("$type") == "com.linkedin.voyager.dash.identity.profile.tetris.PagedListComponent":
                components = item.get("components", {})
                elements = components.get("elements", [])
                
                for element in elements:
                    # Each element contains an entityComponent with the skill details
                    entity_component = element.get("components", {}).get("entityComponent", {})
                    
                    if entity_component:
                        # Extract the skill name from titleV2
                        title_v2 = entity_component.get("titleV2", {})
                        text_obj = title_v2.get("text", {})
                        skill_name = text_obj.get("text")
                        
                        if skill_name:
                            skill_obj = {"name": skill_name}
                            
                            # Try to find the entityUrn from the action component
                            entity_urn = None
                            sub_components = entity_component.get("subComponents", {})
                            sub_component_list = sub_components.get("components", [])
                            
                            for sub_comp in sub_component_list:
                                action_comp = sub_comp.get("components", {}).get("actionComponent", {})
                                if action_comp:
                                    action = action_comp.get("action", {})
                                    endorsed_skill_action = action.get("endorsedSkillAction", {})
                                    if endorsed_skill_action:
                                        # Extract the URN reference (starts with *)
                                        entity_urn = endorsed_skill_action.get("*endorsedSkill")
                                        break
                            
                            # Add entityUrn if found
                            if entity_urn:
                                skill_obj["entityUrn"] = entity_urn
                                
                                # Get endorsement data from the map
                                if entity_urn in endorsed_skills_map:
                                    skill_obj["numEndorsements"] = endorsed_skills_map[entity_urn]["endorsementCount"]
                                    skill_obj["endorsedByViewer"] = endorsed_skills_map[entity_urn]["endorsedByViewer"]
                                else:
                                    skill_obj["numEndorsements"] = 0
                            else:
                                skill_obj["numEndorsements"] = 0
                            
                            skills.append(skill_obj)
        
        return skills

    def get_profile_graphql(self, public_id=None, urn_id=None):
        """Fetch full profile data using GraphQL API (modern approach).

        :param public_id: LinkedIn public ID for a profile
        :type public_id: str, optional
        :param urn_id: LinkedIn URN ID for a profile (e.g., 'ACoAAAS7RzQB5MFgx7URQOOa7dShFKQhfdIWxms')
        :type urn_id: str, optional

        :return: Profile data
        :rtype: dict
        """
        if not public_id and not urn_id:
            raise ValueError("Either public_id or urn_id is required")

        # Construct the profile URN
        if urn_id:
            if not urn_id.startswith("urn:li:fsd_profile:"):
                profile_urn = f"urn:li:fsd_profile:{urn_id}"
            else:
                profile_urn = urn_id
        else:
            # If only public_id is provided, we need to get the URN first
            legacy_profile = self.get_profile(public_id=public_id)
            profile_urn = legacy_profile.get("profile_urn")
            if not profile_urn:
                raise ValueError(f"Could not retrieve profile URN for public_id: {public_id}")

        # GraphQL decoration ID for full profile
        decoration_id = "com.linkedin.voyager.dash.deco.identity.profile.FullProfile-76"
        
        # Construct the URL
        full_url = f"/identity/dash/profiles/{profile_urn}?decorationId={decoration_id}"
        
        # Generate a page instance ID
        random_bytes = bytes([random.randint(0, 255) for _ in range(16)])
        page_instance_id = base64.b64encode(random_bytes).decode('utf-8').rstrip('=')
        page_instance = f"urn:li:page:d_flagship3_profile_view_base;{page_instance_id}"
        
        # Add required headers
        headers = {
            "accept": "application/vnd.linkedin.normalized+json+2.1",
            "x-restli-protocol-version": "2.0.0",
            "x-li-page-instance": page_instance,
            "x-li-track": '{"clientVersion":"1.13.40037","mpVersion":"1.13.40037","osName":"web","timezoneOffset":-4,"timezone":"America/New_York","deviceFormFactor":"DESKTOP","mpName":"voyager-web","displayDensity":2,"displayWidth":6400,"displayHeight":2666}',
            "x-li-lang": "en_US",
            "x-li-deco-include-micro-schema": "true",
        }
        
        res = self._fetch(full_url, headers=headers)
        data = res.json()
        
        # Extract the main profile data
        profile_data = data.get("data", {})
        
        # Parse and clean up the profile data
        profile = {}
        
        # Basic info
        if profile_data.get("firstName"):
            profile["first_name"] = profile_data["firstName"]
        if profile_data.get("lastName"):
            profile["last_name"] = profile_data["lastName"]
        if profile_data.get("headline"):
            profile["headline"] = profile_data["headline"]
        if profile_data.get("summary"):
            profile["summary"] = profile_data["summary"]
        if profile_data.get("publicIdentifier"):
            profile["public_identifier"] = profile_data["publicIdentifier"]
        if profile_data.get("entityUrn"):
            profile["profile_urn"] = profile_data["entityUrn"]
        if profile_data.get("objectUrn"):
            profile["member_urn"] = profile_data["objectUrn"]
        if profile_data.get("trackingId"):
            profile["tracking_id"] = profile_data["trackingId"]
        
        # Premium status
        profile["premium"] = profile_data.get("premium", False)
        profile["show_premium_badge"] = profile_data.get("showPremiumSubscriberBadge", False)
        
        # Location
        location = profile_data.get("location", {})
        if location:
            profile["location"] = {
                "country_code": location.get("countryCode"),
                "postal_code": location.get("postalCode")
            }
        
        geo_location = profile_data.get("geoLocation", {})
        if geo_location:
            profile["geo_location"] = {
                "geo_urn": geo_location.get("geoUrn"),
                "postal_code": geo_location.get("postalCode")
            }
        
        # Profile picture
        profile_picture = profile_data.get("profilePicture", {})
        if profile_picture:
            display_image_ref = profile_picture.get("displayImageReference", {})
            vector_image = display_image_ref.get("vectorImage")
            
            if vector_image:
                root_url = vector_image.get("rootUrl", "")
                artifacts = vector_image.get("artifacts", [])
                
                images = {}
                for artifact in artifacts:
                    width = artifact.get("width")
                    file_segment = artifact.get("fileIdentifyingUrlPathSegment")
                    if width and file_segment:
                        images[f"{width}x{width}"] = f"{root_url}{file_segment}"
                
                if images:
                    profile["profile_picture"] = {
                        "root_url": root_url,
                        "images": images
                    }
        
        # Background picture
        background_picture = profile_data.get("backgroundPicture", {})
        if background_picture:
            display_image_ref = background_picture.get("displayImageReference", {})
            vector_image = display_image_ref.get("vectorImage")
            
            if vector_image:
                root_url = vector_image.get("rootUrl", "")
                artifacts = vector_image.get("artifacts", [])
                
                images = {}
                for artifact in artifacts:
                    width = artifact.get("width")
                    file_segment = artifact.get("fileIdentifyingUrlPathSegment")
                    if width and file_segment:
                        images[f"{width}x{width}"] = f"{root_url}{file_segment}"
                
                if images:
                    profile["background_picture"] = {
                        "root_url": root_url,
                        "images": images
                    }
        
        # Industry
        if profile_data.get("industryUrn"):
            profile["industry_urn"] = profile_data["industryUrn"]
        
        # Birthdate
        birthdate = profile_data.get("birthDateOn")
        if birthdate:
            profile["birthdate"] = {
                "month": birthdate.get("month"),
                "day": birthdate.get("day"),
                "year": birthdate.get("year")
            }
        
        return profile

    def get_available_profile_cards(self, profile_urn, locale="en_US"):
        """Get list of available profile cards for a profile.
        
        This is a lightweight method that returns only the card URNs without
        fetching the full card data.
        
        :param profile_urn: LinkedIn profile URN
        :type profile_urn: str
        :param locale: Locale for the card (default: 'en_US')
        :type locale: str, optional
        
        :return: List of available card types
        :rtype: list
        """
        try:
            response = self.get_profile_card(profile_urn, card_type=None, locale=locale)
            data = response.get('data', {}).get('data', {})
            card_elements = data.get('identityDashProfileCardsByDeferredCards', {}).get('*elements', [])
            
            available_cards = []
            for urn in card_elements:
                # Extract card type from URN like "urn:li:fsd_profileCard:(ID,CARD_TYPE,locale)"
                parts = urn.split(',')
                if len(parts) >= 2:
                    available_cards.append(parts[1])
            
            return available_cards
        except Exception as e:
            self.logger.error(f"Failed to get available profile cards: {e}")
            return []
    
    def get_profile_card(self, profile_urn, card_type=None, locale="en_US"):
        """Fetch profile cards (sections) using GraphQL API.
        
        This method fetches detailed data for profile sections like
        EXPERIENCE, EDUCATION, LICENSES_AND_CERTIFICATIONS, etc.
        
        :param profile_urn: LinkedIn profile URN (e.g., 'ACoAAAvf7-UBk_8MvFoDYosW9PdYq24NTpjzHQA')
        :type profile_urn: str
        :param card_type: Type of card to fetch (optional - if None, fetches all cards)
        :type card_type: str, optional
        :param locale: Locale for the card (default: 'en_US')
        :type locale: str, optional
        
        :return: Profile card data
        :rtype: dict
        
        Available card types:
        - EXPERIENCE: Work history
        - EDUCATION: Education history
        - LICENSES_AND_CERTIFICATIONS: Certifications
        - SKILLS: Skills
        - PROJECTS: Projects
        - VOLUNTEERING_EXPERIENCE: Volunteer work
        - PUBLICATIONS: Publications
        - PATENTS: Patents
        - COURSES: Courses
        - HONORS_AND_AWARDS: Honors and awards
        - TEST_SCORES: Test scores
        - LANGUAGES: Languages
        - ORGANIZATIONS: Organizations
        - RECOMMENDATIONS: Recommendations
        - ABOUT: About section
        - HIGHLIGHTS: Highlights
        - FEATURED: Featured content
        - SERVICES: Services
        - INTERESTS: Interests
        """
        # Clean profile_urn if it doesn't include the full URN prefix
        if not profile_urn.startswith("urn:li:fsd_profile:"):
            profile_urn = f"urn:li:fsd_profile:{profile_urn}"
        
        # GraphQL queryId for profile cards
        query_id = "voyagerIdentityDashProfileCards.2bdab365ea61cd6af00b57e0183430c3"
        
        # Construct the GraphQL URL with proper URL encoding
        # LinkedIn expects the URN to be URL-encoded in the variables parameter
        import urllib.parse
        encoded_urn = urllib.parse.quote(profile_urn, safe='')
        variables = f"(profileUrn:{encoded_urn})"
        full_url = f"/graphql?includeWebMetadata=true&variables={variables}&queryId={query_id}"
        
        # Generate a page instance ID
        random_bytes = bytes([random.randint(0, 255) for _ in range(16)])
        page_instance_id = base64.b64encode(random_bytes).decode('utf-8').rstrip('=')
        page_instance = f"urn:li:page:d_flagship3_profile_view_base;{page_instance_id}"
        
        # Add required headers
        headers = {
            "accept": "application/vnd.linkedin.normalized+json+2.1",
            "x-restli-protocol-version": "2.0.0",
            "x-li-page-instance": page_instance,
            "x-li-pem-metadata": "Voyager - Profile=profile-tab-deferred-cards",
            "x-li-track": '{"clientVersion":"1.13.40037","mpVersion":"1.13.40037","osName":"web","timezoneOffset":-4,"timezone":"America/New_York","deviceFormFactor":"DESKTOP","mpName":"voyager-web","displayDensity":2,"displayWidth":6400,"displayHeight":2666}',
            "x-li-lang": "en_US",
        }
        
        try:
            res = self._fetch(full_url, headers=headers)
            data = res.json()
            
            # Check if included array is empty (deferred loading)
            included = data.get('included', [])
            if not included:
                self.logger.warning(
                    "Response has empty 'included' array. LinkedIn is using deferred loading. "
                    "Card data may need to be fetched separately or with different parameters."
                )
                # Add helpful metadata to the response
                card_elements = data.get('data', {}).get('data', {}).get('identityDashProfileCardsByDeferredCards', {}).get('*elements', [])
                available_cards = []
                for urn in card_elements:
                    parts = urn.split(',')
                    if len(parts) >= 2:
                        available_cards.append(parts[1])
                
                data['_metadata'] = {
                    'note': 'Card data not loaded. This endpoint returns only card references.',
                    'available_cards': available_cards,
                    'suggestion': 'Use specific profile endpoints like get_profile_skills_graphql() or get_profile_contact_info_graphql()'
                }
            
            # If a specific card_type is requested, filter the response
            if card_type:
                return self._filter_profile_card(data, card_type)
            
            return data
        except Exception as e:
            self.logger.error(f"Failed to fetch profile card: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    def _filter_profile_card(self, response_data, card_type):
        """Filter profile cards response to return only the specified card type.
        
        :param response_data: Full GraphQL response
        :type response_data: dict
        :param card_type: Card type to filter (e.g., 'EXPERIENCE', 'EDUCATION')
        :type card_type: str
        
        :return: Filtered response containing only the specified card
        :rtype: dict
        """
        try:
            # First check if the card type exists in the available cards
            data = response_data.get('data', {}).get('data', {})
            card_elements = data.get('identityDashProfileCardsByDeferredCards', {}).get('*elements', [])
            
            # Check if the requested card type is available
            card_urn_pattern = f",{card_type},"
            card_exists = any(card_urn_pattern in urn for urn in card_elements)
            
            if not card_exists:
                available_cards = []
                for urn in card_elements:
                    # Extract card type from URN like "urn:li:fsd_profileCard:(ID,CARD_TYPE,locale)"
                    parts = urn.split(',')
                    if len(parts) >= 2:
                        available_cards.append(parts[1])
                
                self.logger.warning(
                    f"Card type '{card_type}' not found in response. "
                    f"Available cards: {', '.join(available_cards)}"
                )
                return {
                    'data': response_data.get('data'),
                    'included': [],
                    'error': f"Card type '{card_type}' not available for this profile",
                    'available_cards': available_cards
                }
            
            # Filter the included array for the specific card and related entities
            included = response_data.get('included', [])
            filtered_card = None
            related_entities = []
            
            for item in included:
                entity_urn = item.get('entityUrn', '')
                item_type = item.get('$type', '')
                
                # Check if this is the card we're looking for
                if item_type == 'com.linkedin.voyager.dash.identity.profile.tetris.Card' and card_urn_pattern in entity_urn:
                    filtered_card = item
                # Keep related entities (companies, schools, etc.)
                elif item_type in [
                    'com.linkedin.voyager.dash.organization.Company',
                    'com.linkedin.voyager.dash.organization.School',
                    'com.linkedin.voyager.dash.social.SocialDetail',
                    'com.linkedin.voyager.dash.relationships.MemberRelationship'
                ]:
                    related_entities.append(item)
            
            if filtered_card:
                return {
                    'data': response_data.get('data'),
                    'included': [filtered_card] + related_entities
                }
            else:
                # Card exists in URN list but not in included array (might not be expanded yet)
                return {
                    'data': response_data.get('data'),
                    'included': related_entities,
                    'note': f"Card '{card_type}' exists but data not fully loaded. Try fetching all cards first."
                }
                
        except Exception as e:
            self.logger.error(f"Error filtering profile card: {e}")
            return response_data

    """ @deprecated """
    def get_profile(self, public_id=None, urn_id=None):
        """Fetch data for a given LinkedIn profile (LEGACY).

        :param public_id: LinkedIn public ID for a profile
        :type public_id: str, optional
        :param urn_id: LinkedIn URN ID for a profile
        :type urn_id: str, optional

        :return: Profile data
        :rtype: dict
        """
        # NOTE this still works for now, but will probably eventually have to be converted to
        # https://www.linkedin.com/voyager/api/identity/profiles/ACoAAAKT9JQBsH7LwKaE9Myay9WcX8OVGuDq9Uw

        res = self._fetch(f"/identity/profiles/{public_id or urn_id}/profileView")
        
        data = res.json()
        if data and "status" in data and data["status"] != 200:
            self.logger.info("request failed: {}".format(data["message"]))
            return {}

        # massage [profile] data
        profile = data["profile"]
        if "miniProfile" in profile:
            if "picture" in profile["miniProfile"]:
                profile["displayPictureUrl"] = profile["miniProfile"]["picture"][
                    "com.linkedin.common.VectorImage"
                ]["rootUrl"]

                images_data = profile["miniProfile"]["picture"][
                    "com.linkedin.common.VectorImage"
                ]["artifacts"]
                for img in images_data:
                    w, h, url_segment = itemgetter(
                        "width", "height", "fileIdentifyingUrlPathSegment"
                    )(img)
                    profile[f"img_{w}_{h}"] = url_segment

            profile["profile_id"] = get_id_from_urn(profile["miniProfile"]["entityUrn"])
            profile["profile_urn"] = profile["miniProfile"]["entityUrn"]
            profile["member_urn"] = profile["miniProfile"]["objectUrn"]
            profile["public_id"] = profile["miniProfile"]["publicIdentifier"]

            del profile["miniProfile"]

        del profile["defaultLocale"]
        del profile["supportedLocales"]
        del profile["versionTag"]
        del profile["showEducationOnProfileTopCard"]

        # massage [experience] data
        experience = data["positionView"]["elements"]
        for item in experience:
            if "company" in item and "miniCompany" in item["company"]:
                if "logo" in item["company"]["miniCompany"]:
                    logo = item["company"]["miniCompany"]["logo"].get(
                        "com.linkedin.common.VectorImage"
                    )
                    if logo:
                        item["companyLogoUrl"] = logo["rootUrl"]
                del item["company"]["miniCompany"]

        profile["experience"] = experience

        # massage [education] data
        education = data["educationView"]["elements"]
        for item in education:
            if "school" in item:
                if "logo" in item["school"]:
                    item["school"]["logoUrl"] = item["school"]["logo"][
                        "com.linkedin.common.VectorImage"
                    ]["rootUrl"]
                    del item["school"]["logo"]

        profile["education"] = education

        # massage [languages] data
        languages = data["languageView"]["elements"]
        for item in languages:
            del item["entityUrn"]
        profile["languages"] = languages

        # massage [publications] data
        publications = data["publicationView"]["elements"]
        for item in publications:
            del item["entityUrn"]
            for author in item.get("authors", []):
                del author["entityUrn"]
        profile["publications"] = publications

        # massage [certifications] data
        certifications = data["certificationView"]["elements"]
        for item in certifications:
            del item["entityUrn"]
        profile["certifications"] = certifications

        # massage [volunteer] data
        volunteer = data["volunteerExperienceView"]["elements"]
        for item in volunteer:
            del item["entityUrn"]
        profile["volunteer"] = volunteer

        # massage [honors] data
        honors = data["honorView"]["elements"]
        for item in honors:
            del item["entityUrn"]
        profile["honors"] = honors

        # massage [projects] data
        projects = data["projectView"]["elements"]
        for item in projects:
            del item["entityUrn"]
        profile["projects"] = projects

        return profile

    def get_profile_connections(self, urn_id):
        """Fetch first-degree connections for a given LinkedIn profile.

        :param urn_id: LinkedIn URN ID for a profile
        :type urn_id: str

        :return: List of search results
        :rtype: list
        """
        return self.search_people(connection_of=urn_id, network_depth="F")
    
    def get_my_connections(self, count=40, offset=0):
        """Fetch first-degree connections for the currently logged in profile.

        :param count: Number of connections to fetch
        :type count: int
        :param offset: Offset to start fetching connections from
        :type offset: int

        :return: List of dictionaries containing connection details
        :rtype: list
        """

        # Initialize an empty list to store collected connections
        collectedConnections = []

        # Wait for 3 seconds before making the request to avoid hitting rate limits
        sleep(3)
        print(f"Fetching connections, starting from {len(collectedConnections)}")

        # Fetch connections using LinkedIn API endpoint with provided count and offset
        res = self._fetch(f"/relationships/dash/connections?decorationId=com.linkedin.voyager.dash.deco.web.mynetwork.ConnectionListWithProfile-16&count={count}&q=search&sortType=RECENTLY_ADDED&start={offset}")
        data = res.json()

        # Extract elements from the response data
        elements = data.get("elements")
        
        # If no elements are found, print a message and return an empty list
        if not elements:
            print(f"Stopping! Elements list not found. Found: {len(collectedConnections)} connections.")
            return []
        
        # If elements list is empty, print a message and return an empty list
        if len(elements) < 1:
            print(f"Stopping! All connections retrieved. Found: {len(collectedConnections)} connections.")
            return []

        print("completed!")

        # Iterate through the elements to format and collect connections
        for element in elements:
            inner = element.get("connectedMemberResolutionResult")
            if not inner: 
                continue
            formattedProfile = {
                "firstName": inner.get("firstName"),
                "lastName": inner.get("lastName"),
                "profileUrn": inner.get("entityUrn"),
            }
            collectedConnections.append(formattedProfile)

        # Print the number of connections collected and return the list
        print(f"Returning {len(collectedConnections)} connections!")
        return collectedConnections

    def get_company_updates(
        self, public_id=None, urn_id=None, max_results=None, results=None
    ):
        """Fetch company updates (news activity) for a given LinkedIn company.

        :param public_id: LinkedIn public ID for a company
        :type public_id: str, optional
        :param urn_id: LinkedIn URN ID for a company
        :type urn_id: str, optional

        :return: List of company update objects
        :rtype: list
        """

        if results is None:
            results = []

        params = {
            "companyUniversalName": {public_id or urn_id},
            "q": "companyFeedByUniversalName",
            "moduleKey": "member-share",
            "count": Linkedin._MAX_UPDATE_COUNT,
            "start": len(results),
        }

        res = self._fetch(f"/feed/updates", params=params)

        data = res.json()

        if (
            len(data["elements"]) == 0
            or (max_results is not None and len(results) >= max_results)
            or (
                max_results is not None
                and len(results) / max_results >= Linkedin._MAX_REPEATED_REQUESTS
            )
        ):
            return results

        results.extend(data["elements"])
        self.logger.debug(f"results grew: {len(results)}")

        return self.get_company_updates(
            public_id=public_id,
            urn_id=urn_id,
            results=results,
            max_results=max_results,
        )

    def get_profile_updates(
        self, public_id=None, urn_id=None, max_results=None, results=None
    ):
        """Fetch profile updates (newsfeed activity) for a given LinkedIn profile.

        :param public_id: LinkedIn public ID for a profile
        :type public_id: str, optional
        :param urn_id: LinkedIn URN ID for a profile
        :type urn_id: str, optional

        :return: List of profile update objects
        :rtype: list
        """

        if results is None:
            results = []

        params = {
            "profileId": {public_id or urn_id},
            "q": "memberShareFeed",
            "moduleKey": "member-share",
            "count": Linkedin._MAX_UPDATE_COUNT,
            "start": len(results),
        }

        res = self._fetch(f"/feed/updates", params=params)

        data = res.json()

        if (
            len(data["elements"]) == 0
            or (max_results is not None and len(results) >= max_results)
            or (
                max_results is not None
                and len(results) / max_results >= Linkedin._MAX_REPEATED_REQUESTS
            )
        ):
            return results

        results.extend(data["elements"])
        self.logger.debug(f"results grew: {len(results)}")

        return self.get_profile_updates(
            public_id=public_id,
            urn_id=urn_id,
            results=results,
            max_results=max_results,
        )

    def get_current_profile_views(self):
        """Get profile view statistics, including chart data.

        :return: Profile view data
        :rtype: dict
        """
        res = self._fetch(f"/identity/wvmpCards")

        data = res.json()

        return data["elements"][0]["value"][
            "com.linkedin.voyager.identity.me.wvmpOverview.WvmpViewersCard"
        ]["insightCards"][0]["value"][
            "com.linkedin.voyager.identity.me.wvmpOverview.WvmpSummaryInsightCard"
        ][
            "numViews"
        ]

    def get_school(self, public_id):
        """Fetch data about a given LinkedIn school.

        :param public_id: LinkedIn public ID for a school
        :type public_id: str

        :return: School data
        :rtype: dict
        """
        params = {
            "decorationId": "com.linkedin.voyager.deco.organization.web.WebFullCompanyMain-12",
            "q": "universalName",
            "universalName": public_id,
        }

        res = self._fetch(f"/organization/companies?{urlencode(params)}")

        data = res.json()

        if data and "status" in data and data["status"] != 200:
            self.logger.info("request failed: {}".format(data))
            return {}

        school = data["elements"][0]

        return school

    def get_company(self, public_id):
        """Fetch data about a given LinkedIn company.

        :param public_id: LinkedIn public ID for a company
        :type public_id: str

        :return: Company data
        :rtype: dict
        """
        params = {
            "decorationId": "com.linkedin.voyager.deco.organization.web.WebFullCompanyMain-12",
            "q": "universalName",
            "universalName": public_id,
        }

        res = self._fetch(f"/organization/companies", params=params)

        data = res.json()

        if data and "status" in data and data["status"] != 200:
            self.logger.info("request failed: {}".format(data["message"]))
            return {}

        company = data["elements"][0]

        return company

    def get_conversation_details(self, profile_urn_id):
        """Fetch conversation (message thread) details for a given LinkedIn profile.

        :param profile_urn_id: LinkedIn URN ID for a profile
        :type profile_urn_id: str

        :return: Conversation data
        :rtype: dict
        """
        # passing `params` doesn't work properly, think it's to do with List().
        # Might be a bug in `requests`?
        res = self._fetch(
            f"/messaging/conversations?\
            keyVersion=LEGACY_INBOX&q=participants&recipients=List({profile_urn_id})"
        )

        data = res.json()

        if data["elements"] == []:
            return {}

        item = data["elements"][0]
        item["id"] = get_id_from_urn(item["entityUrn"])

        return item

    def get_conversations(self):
        """Fetch list of conversations the user is in.

        :return: List of conversations
        :rtype: list
        """
        params = {"keyVersion": "LEGACY_INBOX"}

        res = self._fetch(f"/messaging/conversations", params=params)

        return res.json()

    def get_conversation(self, conversation_urn_id):
        """Fetch data about a given conversation.

        :param conversation_urn_id: LinkedIn URN ID for a conversation
        :type conversation_urn_id: str

        :return: Conversation data
        :rtype: dict
        """
        res = self._fetch(f"/messaging/conversations/{conversation_urn_id}/events")

        return res.json()

    def send_message(self, message_body, conversation_urn_id=None, recipients=None):
        print('send_message')
        """Send a message to a given conversation.

        :param message_body: Message text to send
        :type message_body: str
        :param conversation_urn_id: LinkedIn URN ID for a conversation
        :type conversation_urn_id: str, optional
        :param recipients: List of profile urn id's
        :type recipients: list, optional

        :return: Error state. If True, an error occured.
        :rtype: boolean
        """
        params = {"action": "create"}

        if not (conversation_urn_id or recipients):
            self.logger.debug("Must provide [conversation_urn_id] or [recipients].")
            return True

        message_event = {
            "eventCreate": {
                "originToken": str(uuid.uuid4()),
                "value": {
                    "com.linkedin.voyager.messaging.create.MessageCreate": {
                        "attributedBody": {
                            "text": message_body,
                            "attributes": [],
                        },
                        "attachments": [],
                    }
                },
                "trackingId": generate_trackingId_as_charString(),
            },
            "dedupeByClientGeneratedToken": False,
        }

        if conversation_urn_id and not recipients:
            res = self._post(
                f"/messaging/conversations/{conversation_urn_id}/events",
                params=params,
                data=json.dumps(message_event),
            )
        elif recipients and not conversation_urn_id:
            print('recipients:', recipients)
            message_event["recipients"] = recipients
            message_event["subtype"] = "MEMBER_TO_MEMBER"
            payload = {
                "keyVersion": "LEGACY_INBOX",
                "conversationCreate": message_event,
            }
            res = self._post(
                f"/messaging/conversations",
                params=params,
                data=json.dumps(payload),
            )
            print('send_message status code:', res.status_code)

        return res.status_code != 201

    def mark_conversation_as_seen(self, conversation_urn_id):
        """Send 'seen' to a given conversation.

        :param conversation_urn_id: LinkedIn URN ID for a conversation
        :type conversation_urn_id: str

        :return: Error state. If True, an error occured.
        :rtype: boolean
        """
        payload = json.dumps({"patch": {"$set": {"read": True}}})

        res = self._post(
            f"/messaging/conversations/{conversation_urn_id}", data=payload
        )

        return res.status_code != 200

    def get_user_profile(self, use_cache=True):
        """Get the current user profile. If not cached, a network request will be fired.

        :return: Profile data for currently logged in user
        :rtype: dict
        """
        me_profile = self.client.metadata.get("me")
        if not self.client.metadata.get("me") or not use_cache:
            res = self._fetch(f"/me")
            me_profile = res.json()
            # cache profile
            self.client.metadata["me"] = me_profile

        return me_profile

    def get_invitations(self, start=0, limit=3):
        """Fetch connection invitations for the currently logged in user.

        :param start: How much to offset results by
        :type start: int
        :param limit: Maximum amount of invitations to return
        :type limit: int

        :return: List of invitation objects
        :rtype: list
        """
        params = {
            "start": start,
            "count": limit,
            "includeInsights": True,
            "q": "receivedInvitation",
        }

        res = self._fetch(
            "/relationships/invitationViews",
            params=params,
        )

        if res.status_code != 200:
            return []

        response_payload = res.json()
        return [element["invitation"] for element in response_payload["elements"]]

    def reply_invitation(
        self, invitation_entity_urn, invitation_shared_secret, action="accept"
    ):
        """Respond to a connection invitation. By default, accept the invitation.

        :param invitation_entity_urn: URN ID of the invitation
        :type invitation_entity_urn: int
        :param invitation_shared_secret: Shared secret of invitation
        :type invitation_shared_secret: str
        :param action: "accept" or "reject". Defaults to "accept"
        :type action: str, optional

        :return: Success state. True if successful
        :rtype: boolean
        """
        invitation_id = get_id_from_urn(invitation_entity_urn)
        params = {"action": action}
        payload = json.dumps(
            {
                "invitationId": invitation_id,
                "invitationSharedSecret": invitation_shared_secret,
                "isGenericInvitation": False,
            }
        )

        res = self._post(
            f"{self.client.API_BASE_URL}/relationships/invitations/{invitation_id}",
            params=params,
            data=payload,
        )

        return res.status_code == 200

    def add_connection(self, profile_public_id: str, message="", profile_urn=None):
        """Add a given profile id as a connection.

        :param profile_public_id: public ID of a LinkedIn profile
        :type profile_public_id: str
        :param message: message to send along with connection request
        :type profile_urn: str, optional
        :param profile_urn: member URN for the given LinkedIn profile
        :type profile_urn: str, optional

        :return: Error state. True if error occurred
        :rtype: boolean
        """

        # Validating message length (max size is 300 characters)
        if len(message) > 300:
            self.logger.info("Message too long. Max size is 300 characters")
            return False

        if not profile_urn:
            profile_urn_string = self.get_profile(public_id=profile_public_id)[
                "profile_urn"
            ]
            # Returns string of the form 'urn:li:fs_miniProfile:ACoAACX1hoMBvWqTY21JGe0z91mnmjmLy9Wen4w'
            # We extract the last part of the string
            profile_urn = profile_urn_string.split(":")[-1]

        payload = {
            "invitee": {
                "inviteeUnion": {"memberProfile": f"urn:li:fsd_profile:{profile_urn}"}
            },
            "customMessage": message,
        }
        params = {
            "action": "verifyQuotaAndCreateV2",
            "decorationId": "com.linkedin.voyager.dash.deco.relationships.InvitationCreationResultWithInvitee-2",
        }

        res = self._post(
            "/voyagerRelationshipsDashMemberRelationships",
            data=json.dumps(payload),
            headers={"accept": "application/vnd.linkedin.normalized+json+2.1"},
            params=params,
        )
        # Check for connection_response.status_code == 400 and connection_response.json().get('data', {}).get('code') == 'CANT_RESEND_YET'
        # If above condition is True then request has been already sent, (might be pending or already connected)
        print('status code:', res.status_code)
        # 406 means already sent request so we return false because not an error 
        if res.status_code == 406:
            return False
        if res.status_code == 429:
            return 429
        if res.ok:
            return False
        else:
            return True

    def remove_connection(self, public_profile_id):
        """Remove a given profile as a connection.

        :param public_profile_id: public ID of a LinkedIn profile
        :type public_profile_id: str

        :return: Error state. True if error occurred
        :rtype: boolean
        """
        res = self._post(
            f"/identity/profiles/{public_profile_id}/profileActions?action=disconnect",
            headers={"accept": "application/vnd.linkedin.normalized+json+2.1"},
        )

        return res.status_code != 200

    def track(self, eventBody, eventInfo):
        payload = {"eventBody": eventBody, "eventInfo": eventInfo}
        res = self._post(
            "/li/track",
            base_request=True,
            headers={
                "accept": "*/*",
                "content-type": "text/plain;charset=UTF-8",
            },
            data=json.dumps(payload),
        )

        return res.status_code != 200

    def view_profile(
        self,
        target_profile_public_id,
        target_profile_member_urn_id=None,
        network_distance=None,
    ):
        """View a profile, notifying the user that you "viewed" their profile.

        Provide [target_profile_member_urn_id] and [network_distance] to save 2 network requests and
        speed up the execution of this function.

        :param target_profile_public_id: public ID of a LinkedIn profile
        :type target_profile_public_id: str
        :param network_distance: How many degrees of separation exist e.g. 2
        :type network_distance: int, optional
        :param target_profile_member_urn_id: member URN id for target profile
        :type target_profile_member_urn_id: str, optional

        :return: Error state. True if error occurred
        :rtype: boolean
        """
        me_profile = self.get_user_profile()

        if not target_profile_member_urn_id:
            profile = self.get_profile(public_id=target_profile_public_id)
            target_profile_member_urn_id = int(get_id_from_urn(profile["member_urn"]))

        if not network_distance:
            profile_network_info = self.get_profile_network_info(
                public_profile_id=target_profile_public_id
            )
            network_distance = int(
                profile_network_info["distance"]
                .get("value", "DISTANCE_2")
                .split("_")[1]
            )

        viewer_privacy_setting = "F"
        me_member_id = me_profile["plainId"]

        client_application_instance = self.client.metadata["clientApplicationInstance"]

        eventBody = {
            "viewerPrivacySetting": viewer_privacy_setting,
            "networkDistance": network_distance,
            "vieweeMemberUrn": f"urn:li:member:{target_profile_member_urn_id}",
            "profileTrackingId": self.client.metadata["clientPageInstanceId"],
            "entityView": {
                "viewType": "profile-view",
                "viewerId": me_member_id,
                "targetId": target_profile_member_urn_id,
            },
            "header": {
                "pageInstance": {
                    "pageUrn": "urn:li:page:d_flagship3_profile_view_base",
                    "trackingId": self.client.metadata["clientPageInstanceId"],
                },
                "time": int(time()),
                "version": client_application_instance["version"],
                "clientApplicationInstance": client_application_instance,
            },
            "requestHeader": {
                "interfaceLocale": "en_US",
                "pageKey": "d_flagship3_profile_view_base",
                "path": f"/in/{target_profile_member_urn_id}/",
                "referer": "https://www.linkedin.com/feed/",
            },
        }

        return self.track(
            eventBody,
            {
                "appId": "com.linkedin.flagship3.d_web",
                "eventName": "ProfileViewEvent",
                "topicName": "ProfileViewEvent",
            },
        )

    def get_profile_privacy_settings(self, public_profile_id):
        """Fetch privacy settings for a given LinkedIn profile.

        :param public_profile_id: public ID of a LinkedIn profile
        :type public_profile_id: str

        :return: Privacy settings data
        :rtype: dict
        """
        res = self._fetch(
            f"/identity/profiles/{public_profile_id}/privacySettings",
            headers={"accept": "application/vnd.linkedin.normalized+json+2.1"},
        )
        if res.status_code != 200:
            return {}

        data = res.json()
        return data.get("data", {})

    def get_profile_member_badges(self, public_profile_id):
        """Fetch badges for a given LinkedIn profile.

        :param public_profile_id: public ID of a LinkedIn profile
        :type public_profile_id: str

        :return: Badges data
        :rtype: dict
        """
        res = self._fetch(
            f"/identity/profiles/{public_profile_id}/memberBadges",
            headers={"accept": "application/vnd.linkedin.normalized+json+2.1"},
        )
        if res.status_code != 200:
            return {}

        data = res.json()
        return data.get("data", {})

    def get_profile_network_info(self, public_profile_id):
        """Fetch network information for a given LinkedIn profile.

        :param public_profile_id: public ID of a LinkedIn profile
        :type public_profile_id: str

        :return: Network data
        :rtype: dict
        """
        res = self._fetch(
            f"/identity/profiles/{public_profile_id}/networkinfo",
            headers={"accept": "application/vnd.linkedin.normalized+json+2.1"},
        )
        if res.status_code != 200:
            return {}

        data = res.json()
        return data.get("data", {})

    def unfollow_entity(self, urn_id):
        """Unfollow a given entity.

        :param urn_id: URN ID of entity to unfollow
        :type urn_id: str

        :return: Error state. Returns True if error occurred
        :rtype: boolean
        """
        payload = {"urn": f"urn:li:fs_followingInfo:{urn_id}"}
        res = self._post(
            "/feed/follows?action=unfollowByEntityUrn",
            headers={"accept": "application/vnd.linkedin.normalized+json+2.1"},
            data=json.dumps(payload),
        )

        err = False
        if res.status_code != 200:
            err = True

        return err

    def _get_list_feed_posts_and_list_feed_urns(
        self, limit=-1, offset=0, exclude_promoted_posts=True
    ):
        """Get a list of URNs from feed sorted by 'Recent' and a list of yet
        unsorted posts, each one of them containing a dict per post.

        :param limit: Maximum length of the returned list, defaults to -1 (no limit)
        :type limit: int, optional
        :param offset: Index to start searching from
        :type offset: int, optional
        :param exclude_promoted_posts: Exclude from the output promoted posts
        :type exclude_promoted_posts: bool, optional

        :return: List of posts and list of URNs
        :rtype: (list, list)
        """
        _PROMOTED_STRING = "Promoted"
        _PROFILE_URL = f"{self.client.LINKEDIN_BASE_URL}/in/"

        l_posts = []
        l_urns = []

        # If count>100 API will return HTTP 400
        count = Linkedin._MAX_UPDATE_COUNT
        if limit == -1:
            limit = Linkedin._MAX_UPDATE_COUNT

        # 'l_urns' equivalent to other functions 'results' variable
        l_urns = []

        while True:
            # when we're close to the limit, only fetch what we need to
            if limit > -1 and limit - len(l_urns) < count:
                count = limit - len(l_urns)
            params = {
                "count": str(count),
                "q": "chronFeed",
                "start": len(l_urns) + offset,
            }
            res = self._fetch(
                f"/feed/updatesV2",
                params=params,
                headers={"accept": "application/vnd.linkedin.normalized+json+2.1"},
            )
            """
            Response includes two keya:
            - ['Data']['*elements']. It includes the posts URNs always
            properly sorted as 'Recent', including yet sponsored posts. The
            downside is that fetching one by one the posts is slower. We will
            save the URNs to later on build a sorted list of posts purging
            promotions
            - ['included']. List with all the posts attributes, but not sorted as
            'Recent' and including promoted posts
            """
            l_raw_posts = res.json().get("included", {})
            l_raw_urns = res.json().get("data", {}).get("*elements", [])

            l_new_posts = parse_list_raw_posts(
                l_raw_posts, self.client.LINKEDIN_BASE_URL
            )
            l_posts.extend(l_new_posts)

            l_urns.extend(parse_list_raw_urns(l_raw_urns))

            # break the loop if we're done searching
            # NOTE: we could also check for the `total` returned in the response.
            # This is in data["data"]["paging"]["total"]
            if (
                (limit > -1 and len(l_urns) >= limit)  # if our results exceed set limit
                or len(l_urns) / count >= Linkedin._MAX_REPEATED_REQUESTS
            ) or len(l_raw_urns) == 0:
                break

            self.logger.debug(f"results grew to {len(l_urns)}")

        return l_posts, l_urns

    def get_feed_posts(self, limit=-1, offset=0, exclude_promoted_posts=True):
        """Get a list of URNs from feed sorted by 'Recent'

        :param limit: Maximum length of the returned list, defaults to -1 (no limit)
        :type limit: int, optional
        :param offset: Index to start searching from
        :type offset: int, optional
        :param exclude_promoted_posts: Exclude from the output promoted posts
        :type exclude_promoted_posts: bool, optional

        :return: List of URNs
        :rtype: list
        """
        l_posts, l_urns = self._get_list_feed_posts_and_list_feed_urns(
            limit, offset, exclude_promoted_posts
        )
        return get_list_posts_sorted_without_promoted(l_urns, l_posts)

    def get_job(self, job_id):
        """Fetch data about a given job.
        :param job_id: LinkedIn job ID
        :type job_id: str

        :return: Job data
        :rtype: dict
        """
        params = {
            "decorationId": "com.linkedin.voyager.deco.jobs.web.shared.WebLightJobPosting-23",
        }

        res = self._fetch(f"/jobs/jobPostings/{job_id}", params=params)

        data = res.json()

        if data and "status" in data and data["status"] != 200:
            self.logger.info("request failed: {}".format(data["message"]))
            return {}

        return data
